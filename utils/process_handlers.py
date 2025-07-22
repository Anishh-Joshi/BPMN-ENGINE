import os
import json

import os
import json

USERS_DIR = os.path.join(os.getcwd(), "users")
USERS_FILE = os.path.join(USERS_DIR, "users.json")

def save_user(user_data):
    os.makedirs(USERS_DIR, exist_ok=True)  # ✅ Make sure 'users' folder exists

    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
    else:
        users = []

    users.append(user_data)

    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def handle_generic_registration(variables):
    if variables.get("is_valid_registration") is True:
        # Remove validation-only keys if desired
        filtered = {
            k: v for k, v in variables.items()
            if not (k.startswith("is_valid_") or k.startswith("is_"))
        }
        save_user(filtered)
        return {"status": "✅ User data saved", "fields": list(filtered.keys())}
    return {"status": "❌ Not saved. Registration invalid."}

PROCESS_HANDLERS = {
    "UserRegistrationApproval": handle_generic_registration,
    "UserRegistrationAuto": handle_generic_registration
}
