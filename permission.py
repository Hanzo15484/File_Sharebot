# permissions.py

from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import json
import os

OWNER_ID = 5373577888

# Try to import admin helpers from possible places (robust for different project layouts)
cleanup_fn = None
load_admins_full_fn = None

try:
    # prefer dedicated admin_system if present
    from shared_functions import load_admins_full as _laf, cleanup_expired_admins as _clean
    load_admins_full_fn = _laf
    cleanup_fn = _clean
except Exception:
    try:
        # maybe you kept admin helpers in mkadmin
        from mkadmin import load_admins_full as _laf, cleanup_expired_admins as _clean
        load_admins_full_fn = _laf
        cleanup_fn = _clean
    except Exception:
        try:
            # fallback to shared_functions (if you added load_admins_full there)
            from mkadmin import load_admins_full as _laf, load_admins as _legacy
            load_admins_full_fn = _laf
            # no cleanup in shared_functions in many setups
        except Exception:
            # final fallback: read admins.json directly
            load_admins_full_fn = None
            cleanup_fn = None


def _read_admins_json():
    """Fallback reader if no helper imported: read admins.json and return dict-style."""
    try:
        with open("admins.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                data.setdefault("admins", [])
                data.setdefault("expiry", {})
                return data
            # if file is a list (legacy), convert to dict form
            if isinstance(data, list):
                return {"admins": data, "expiry": {}}
    except Exception:
        pass
    return {"admins": [], "expiry": {}}


def _get_user_id_from_update(update: Update):
    """Robustly get user id from different update types."""
    try:
        if update.effective_user:
            return update.effective_user.id
    except Exception:
        pass
    # callback_query
    try:
        if update.callback_query and update.callback_query.from_user:
            return update.callback_query.from_user.id
    except Exception:
        pass
    return None


def _reply_not_authorized(update: Update):
    """
    Reply to the user in the most appropriate way:
    - callback_query -> answer popup
    - message -> reply_text
    - fallback -> try to send message to chat id
    """
    async def _inner(context=None):
        try:
            if update.callback_query:
                # show alert popup for callbacks
                await update.callback_query.answer("You are not authorized to use this command!", show_alert=True)
                return
        except Exception:
            pass

        try:
            if update.message:
                print("You are not authorized to use this command!")
                return
        except Exception:
            pass

        # last resort: do nothing silently
        return

    return _inner


def CheckBotAdmin():
    """
    Decorator factory to protect admin-only handlers.
    Usage:
        from permissions import CheckBotAdmin
        @CheckBotAdmin()
        async def some_handler(update, context): ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):

            # attempt cleanup of expired admins if function available
            try:
                if cleanup_fn:
                    # cleanup may be sync or async; handle both
                    res = cleanup_fn()
                    # if cleanup_fn is a coroutine, schedule/await it
                    if hasattr(res, "__await__"):
                        await res
            except Exception:
                # ignore cleanup errors to avoid blocking handler
                pass

            # load admins via imported helper or fallback reader
            try:
                if load_admins_full_fn:
                    data = load_admins_full_fn()
                    # function may be async; handle
                    if hasattr(data, "__await__"):
                        data = await data
                else:
                    data = _read_admins_json()
            except Exception:
                # fallback
                data = _read_admins_json()

            # normalize: data can be dict or list (legacy)
            if isinstance(data, dict):
                admins = data.get("admins", [])
            elif isinstance(data, list):
                admins = data
            else:
                admins = []

            user_id = _get_user_id_from_update(update)
            if user_id is None:
                # cannot determine user -> deny safely
                await _reply_not_authorized(update)()
                return

            # owner always allowed
            if user_id == OWNER_ID:
                return await func(update, context, *args, **kwargs)

            # check membership
            try:
                if int(user_id) not in [int(x) for x in admins]:
                    await _reply_not_authorized(update)()
                    return
            except Exception:
                # malformed admins list -> deny
                await _reply_not_authorized(update)()
                return

            # allowed -> call the original handler
            return await func(update, context, *args, **kwargs)

        return wrapper
    return decorator
