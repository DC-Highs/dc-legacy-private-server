# Screenshots

The documentation has marked spots (blocks starting with "📸 **Screenshot needed**") where a
picture of the system belongs. Take the screenshots, save them in this folder with the names
below, and replace each marked block with the image line it suggests.

Tips: use a 1280×800 window, a dark browser theme matches the app, and use throw-away accounts
(do not show real emails).

| File | Where it goes | What to capture |
|---|---|---|
| `game.png` | `README.md` | The game running full screen under the header, on the island (after the tutorial). |
| `register.png` | `README.md` | The sign-up page, ideally with the "Passwords do not match" error showing. |
| `admin-users.png` | `README.md`, `administration.md` | `/admin` with the users table and a few accounts. |
| `admin-header.png` | `administration.md` | The header of a logged-in administrator with the "Admin" button. |
| `admin-create-user.png` | `administration.md` | The "New user" dialog. |
| `admin-manage-user.png` | `administration.md` | The "Manage" dialog of a user. |
| `compose-ps.png` | `deployment.md` | `docker compose ps` with the three services `healthy`. |

Find every marked spot with: `grep -rn "Screenshot needed" README.md docs`.
