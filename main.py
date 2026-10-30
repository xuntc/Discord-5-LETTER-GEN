import os
import sys
import time
import random
import string
import requests
import json
from colorama import Fore, init
from configparser import ConfigParser

init(autoreset=True)

# === Paths & Config ===
dir_path = os.path.dirname(os.path.realpath(__file__))
config_path = os.path.join(dir_path, "config.ini")
tokens_path = os.path.join(dir_path, "tokens.txt")
available_file = os.path.join(dir_path, "available_usernames.txt")

# Create config if missing
if not os.path.exists(config_path):
    cfg = ConfigParser()
    cfg["sys"] = {"TOKEN": "", "MULTI_TOKEN": "False", "WEBHOOK_URL": ""}
    cfg["config"] = {"string": "True", "digits": "True", "punctuation": "True", "default_delay": "2.0"}
    with open(config_path, "w") as f:
        cfg.write(f)

configur = ConfigParser()
configur.read(config_path)

# === Global Vars ===
try:
    Delay = configur.getfloat("config", "default_delay")
except:
    Delay = 2.0

current_token_index = 0
user_info_cache = None

# === ANSI Colors ===
Lb = Fore.LIGHTBLACK_EX
Ly = Fore.LIGHTYELLOW_EX
Lg = Fore.LIGHTGREEN_EX
R = Fore.RED
RESET = Fore.RESET  # Global RESET

# === Gradient Banner ===
def print_banner():
    os.system("cls" if os.name == "nt" else "clear")
    
    art = [
            "███████╗ ███████╗  ██████╗  ███╗   ██╗",
            "╚══███╔╝ ██╔════╝ ██╔═══██╗ ████╗  ██║",
            "  ███╔╝  █████╗   ██║   ██║ ██╔██╗ ██║",
            " ███╔╝   ██╔══╝   ██║   ██║ ██║╚██╗██║",
            "███████╗ ███████╗ ╚██████╔╝ ██║ ╚████║",
            "╚══════╝ ╚══════╝  ╚═════╝  ╚═╝  ╚═══╝"
    ]
    
    subtitle = "Discord Username Gen | Made By ZEON | Discord : xuntc"
    colors = [(200, 20, 20), (150, 0, 0), (100, 0, 0)]
    
    def lerp(a, b, t): 
        return int(a + (b - a) * t)
    
    def rgb(r, g, b): 
        return f"\033[38;2;{r};{g};{b}m"
    
    TERM_RESET = "\033[0m"  # Local reset for banner only
    try:
        term_width = os.get_terminal_size().columns
    except:
        term_width = 100

    print("\n")
    for i, line in enumerate(art):
        t = i / max(len(art) - 1, 1)
        if t < 0.5:
            r, g, b = [lerp(colors[0][j], colors[1][j], t * 2) for j in range(3)]
        else:
            r, g, b = [lerp(colors[1][j], colors[2][j], (t - 0.5) * 2) for j in range(3)]
        colored_line = rgb(r, g, b) + line.center(term_width) + TERM_RESET
        print(colored_line)
    print(f"\n{Lb}{subtitle.center(term_width)}{RESET}\n")

# === Token Input ===
def get_token_input():
    tokens = []
    
    # Check if tokens.txt exists
    if os.path.exists(tokens_path):
        with open(tokens_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                # Support both raw tokens AND email:pass:token format
                parts = line.split(":")
                if len(parts) >= 3:
                    # Assume format: email:password:token → take last part
                    token = parts[-1]
                else:
                    # Assume it's a raw token
                    token = line
                if token and all(c in (string.ascii_letters + string.digits + "._-") for c in token):
                    tokens.append(token)
    
    # Prompt user
    print(f"\n{Ly}Please paste your Discord token or type '{Lg}M{Ly}' to use tokens from tokens.txt:{RESET}")
    user_input = input(f"{Lb}> {RESET}").strip()

    if user_input.lower() == "m":
        if not tokens:
            print(f"{R}[-] No valid tokens found in tokens.txt (expected 'email:pass:token' or raw token).{RESET}")
            sys.exit(1)
        print(f"{Lg}[+] Loaded {len(tokens)} token(s) from tokens.txt.{RESET}")
        return tokens, True

    elif user_input:
        # Also support pasting email:pass:token directly
        parts = user_input.split(":", 2)
        if len(parts) >= 3:
            token = parts[2]
        else:
            token = user_input
        print(f"{Lg}[+] Using single token mode.{RESET}")
        return [token], False

    else:
        print(f"{R}[-] No token provided.{RESET}")
        sys.exit(1)

# === Auth Header (FIXED: removed trailing spaces) ===
def get_headers(token):
    return {
        "Authorization": token,
        "Content-Type": "application/json",
        "Origin": "https://discord.com"
    }

# === Get User Info ===
def get_user_info(token):
    global user_info_cache
    if user_info_cache:
        return user_info_cache
    resp = requests.get("https://discord.com/api/v9/users/@me", headers=get_headers(token), timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        user_info_cache = (data.get("username", "Unknown"), data.get("discriminator", "0000"))
        return user_info_cache
    else:
        print(f"{R}[-] Invalid token or network error (HTTP {resp.status_code}).{RESET}")
        sys.exit(1)

# === Webhook Sender ===
def send_webhook(username, url):
    if not url or not url.strip():
        return
    payload = {
        "username": "USERNAME MADE BY ZEON",
        "avatar_url": "https://cdn.icon-icons.com/icons2/488/PNG/512/search_47686.png",
        "embeds": [{
            "title": f"Username `{username}` is available ✅",
            "color": 16768000,
            "footer": {"text": "Discord Username GEN"}
        }]
    }
    try:
        requests.post(url.strip(), json=payload, timeout=5)
    except:
        pass  # Silent fail

# === Core GEN with Token Rotation ===
def validate_username(username, tokens, webhook_url):
    global current_token_index
    max_retries = len(tokens)
    attempts = 0

    while attempts < max_retries:
        token = tokens[current_token_index % len(tokens)]
        body = {"username": username}
        try:
            resp = requests.post(
                "https://discord.com/api/v9/users/@me/pomelo-attempt",
                headers=get_headers(token),
                json=body,
                timeout=10
            )
            data = resp.json()

            if resp.status_code == 200 and data.get("taken") is False:
                print(f"{Lg}[+] '{username}' is available!")
                with open(available_file, "a", encoding="utf-8") as f:
                    f.write(username + "\n")
                send_webhook(username, webhook_url)
                return True

            elif resp.status_code == 429:
                retry_after = data.get("retry_after", 5)
                print(f"{R}[!] Rate limited on token {current_token_index}. Switching token...{RESET}")
                current_token_index += 1
                attempts += 1
                time.sleep(1)
                continue

            else:
                print(f"{R}[-] '{username}' is taken or error occurred.{RESET}")
                return False

        except Exception as e:
            print(f"{R}[-] Request failed: {e}{RESET}")
            current_token_index += 1
            attempts += 1
            time.sleep(1)

    print(f"{R}[-] All tokens rate-limited or failed for '{username}'.{RESET}")
    return False

# === Main Menu ===
def main():
    print_banner()
    tokens, multi_mode = get_token_input()
    webhook_url = configur.get("sys", "WEBHOOK_URL", fallback="").strip()

    # Validate first token
    username, disc = get_user_info(tokens[0])
    print(f"{Lg}Connected as: {Ly}{username}#{disc}{RESET}\n")

    print(f"{Lg}1.{RESET} Generate and check random usernames")
    print(f"{Lg}2.{RESET} Check from usernames.txt")
    choice = input(f"\n{Ly}Select an option (1/2): {RESET}").strip()

    if choice == "1":
        try:
            length = int(input(f"{Ly}Username length (2-32): {RESET}"))
            count = int(input(f"{Ly}How many to generate: {RESET}"))
        except ValueError:
            print(f"{R}[-] Invalid number.{RESET}")
            return
        if not (2 <= length <= 32):
            print(f"{R}[-] Username length must be between 2 and 32.{RESET}")
            return

        chars = ""
        if configur.getboolean("config", "string", fallback=True):
            chars += string.ascii_lowercase
        if configur.getboolean("config", "digits", fallback=True):
            chars += string.digits
        if configur.getboolean("config", "punctuation", fallback=True):
            chars += "_."
        if not chars:
            chars = string.ascii_lowercase + string.digits + "_."
        
        for _ in range(count):
            name = ''.join(random.choices(chars, k=length))
            validate_username(name, tokens, webhook_url)
            time.sleep(Delay)

    elif choice == "2":
        list_path = os.path.join(dir_path, "usernames.txt")
        if not os.path.exists(list_path):
            print(f"{R}[-] usernames.txt not found.{RESET}")
            return
        with open(list_path, "r", encoding="utf-8") as f:
            names = [line.strip() for line in f if line.strip()]
        for name in names:
            validate_username(name, tokens, webhook_url)
            time.sleep(Delay)
    else:
        print(f"{R}[-] Invalid option.{RESET}")
        return

    print(f"\n{Lg}[+] Done! Available usernames saved to 'available_usernames.txt'{RESET}")

if __name__ == "__main__":
    main()