# Start here: connect to your cloud development computer

This guide connects your computer to the company development VM. All code, builds, Docker containers, Claude Code, and Codex run on the VM. Your computer only needs a web browser, a terminal, and an internet connection.

## Connection details

- Server name: `dev-developer-01`
- Server address: `2.28.8.0`
- Linux username: `developer`
- Browser IDE: `http://127.0.0.1:8080`
- Expected SSH fingerprint: `SHA256:R16asW4ceVyV1KxVGHoMyPxrseNFYVanmb9qtbkT+ms`

Do not share your private SSH key with anyone. Only send the file ending in `.pub` to the administrator.

## Step 1: Check that SSH is installed

### Windows

Open **PowerShell** and run:

```powershell
ssh -V
```

If Windows says that `ssh` is not recognized, install **OpenSSH Client** from:

```text
Settings → System → Optional Features → View Features → OpenSSH Client
```

### macOS or Linux

Open **Terminal** and run:

```bash
ssh -V
```

SSH is normally already installed.

## Step 2: Create your personal SSH key

This key proves that you are allowed to access the VM.

### Windows PowerShell

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.ssh"
ssh-keygen -t ed25519 -a 100 -f "$env:USERPROFILE\.ssh\consulting-dev"
```

### macOS or Linux

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
ssh-keygen -t ed25519 -a 100 -f ~/.ssh/consulting-dev
```

When asked for a passphrase, use a password you can remember. Do not send the passphrase to anyone.

This creates two files:

```text
consulting-dev       Private key. Never send or upload this file.
consulting-dev.pub   Public key. Send this file to the administrator.
```

## Step 3: Send your public key to the administrator

Display the public key:

### Windows PowerShell

```powershell
Get-Content "$env:USERPROFILE\.ssh\consulting-dev.pub"
```

### macOS or Linux

```bash
cat ~/.ssh/consulting-dev.pub
```

Send the complete single line to the administrator. It should begin with `ssh-ed25519`.

Wait for the administrator to confirm that your public key has been added to the VM before continuing.

### How the SSH key is configured

SSH uses two matching files:

```text
Your computer: ~/.ssh/consulting-dev
VM:            /home/developer/.ssh/authorized_keys
```

Your computer keeps the private key. The administrator adds the contents of your `.pub` file to the VM's `authorized_keys` file.

SSH will not ask you to choose or paste the key when connecting. The `-i ~/.ssh/consulting-dev` part of the connection command selects it automatically. SSH will ask for a passphrase only if you assigned one while creating the key.

If the connection succeeds without asking for a passphrase, the key is probably configured correctly and was created without a passphrase. That is different from connecting without a key.

## Step 4: Connect using the full command

You can connect without creating an SSH configuration file. This is the most reliable first-time method.

Open PowerShell or Terminal and run:

```bash
ssh -N \
  -i ~/.ssh/consulting-dev \
  -L 8080:127.0.0.1:8080 \
  -L 3000:127.0.0.1:3000 \
  -L 5173:127.0.0.1:5173 \
  developer@2.28.8.0
```

On Windows PowerShell, use this version:

```powershell
ssh -N `
  -i "$env:USERPROFILE\.ssh\consulting-dev" `
  -L 8080:127.0.0.1:8080 `
  -L 3000:127.0.0.1:3000 `
  -L 5173:127.0.0.1:5173 `
  developer@2.28.8.0
```

The first connection will show a server fingerprint. Continue only if it exactly matches:

```text
SHA256:R16asW4ceVyV1KxVGHoMyPxrseNFYVanmb9qtbkT+ms
```

Type `yes`, enter your SSH-key passphrase, and leave the terminal window open.

The command normally displays no message after connecting. A blank terminal means the secure tunnel is working.

To verify which key SSH is using, add `-v` immediately after `ssh` in the command. Look for messages similar to:

```text
Offering public key: /Users/yourname/.ssh/consulting-dev
Authenticated to 2.28.8.0 using "publickey".
```

## Step 5: Optional short connection command

The full command above always works independently of SSH configuration. If you want to use the shorter `ssh -N consulting-dev` command, create an SSH configuration file as follows.

### Windows

Run:

```powershell
notepad "$env:USERPROFILE\.ssh\config"
```

### macOS or Linux

Run:

```bash
nano ~/.ssh/config
```

Add this block and save the file:

```text
Host consulting-dev
    HostName 2.28.8.0
    User developer
    IdentityFile ~/.ssh/consulting-dev
    IdentitiesOnly yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ExitOnForwardFailure yes
    LocalForward 8080 127.0.0.1:8080
    LocalForward 3000 127.0.0.1:3000
    LocalForward 5173 127.0.0.1:5173
```

On macOS or Linux, secure the files:

```bash
chmod 600 ~/.ssh/config ~/.ssh/consulting-dev
```

Test that SSH can read the alias:

```bash
ssh -G consulting-dev | head
```

If that command reports that it cannot resolve `consulting-dev`, the configuration was not saved at the correct path. Use the full connection command from Step 4.

After the alias works, connect with:

```bash
ssh -N consulting-dev
```

## Step 6: Open the development environment

Open Chrome, Edge, Firefox, or Safari and visit:

```text
http://127.0.0.1:8080
```

You should see the browser-based code editor. No source code needs to be downloaded to your personal computer.

Application previews commonly appear at:

```text
http://127.0.0.1:3000
http://127.0.0.1:5173
```

These addresses only work while the SSH tunnel is running.

If GitHub is not connected, run:

```bash
gh auth login
```

Choose **GitHub.com**, **HTTPS**, and **Login with a web browser**. Use your individual company-approved GitHub account with MFA.

If Claude or Codex asks you to sign in, use your individually assigned company account. Do not use or request another person's password or API key.

## Your normal workday

1. Open PowerShell or Terminal.
2. Run the full SSH command from Step 4 and leave it open. If you configured the optional alias, run `ssh -N consulting-dev` instead.
3. Open `http://127.0.0.1:8080` in your browser.
4. Work normally in the browser editor.
5. When finished, save and push your work.
6. Return to the local terminal and press `Ctrl+C` to close the tunnel.

## Troubleshooting

### `Permission denied (publickey)`

- Confirm that the administrator added your `.pub` key.
- Confirm that the `IdentityFile` path points to `consulting-dev`, not `consulting-dev.pub`.
- Never send the private key to troubleshoot this error.

### `Connection timed out`

- Confirm that you have internet access.
- Disable any VPN temporarily and retry.
- Ask the administrator whether the server firewall permits your current network.

### `Address already in use`

Another tunnel is probably already running. Close the other PowerShell or Terminal window, or stop its SSH command with `Ctrl+C`, then retry.

### The browser cannot open `127.0.0.1:8080`

- Confirm that `ssh -N consulting-dev` is still running.
- Check the tunnel terminal for an error.
- Close the tunnel, reconnect, and refresh the browser.

### The application uses a different port

Do not make the port public. Ask the administrator to add another `LocalForward` line to the SSH configuration.

## Security rules

- Never share your private SSH key, passwords, authentication codes, or API keys.
- Never expose development ports directly to the public internet.
- Keep client secrets out of Git and AI prompts unless the project rules explicitly permit their use.
- Use only company-approved GitHub, Anthropic, and OpenAI accounts.
- Push completed work to the company repository regularly. The VM is a working environment, not the only backup.
