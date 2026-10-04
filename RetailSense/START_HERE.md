# RetailSense — start here (Hinglish)

## Fastest method

Extract the entire ZIP, then double-click **START_WINDOWS.bat** beside the RetailSense folder. It handles the correct working directory, creates .venv and installs dependencies. When the server starts, open http://127.0.0.1:5000 → Get started → create a local account → Load demo dataset. Keep the launcher window open. Stop your old app first with Ctrl+C.

## Manual VS Code method

1. ZIP par right-click → **Extract All**. ZIP ke andar se app run mat karo.
2. VS Code → File → Open Folder → **RetailSense** folder select karo.
3. Explorer mein `app.py`, `requirements.txt`, `static` aur `templates` dikhne chahiye.
4. Terminal → New Terminal. Windows PowerShell mein ye commands ek-ek karke chalao:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

5. Browser mein **http://127.0.0.1:5000** kholo. Terminal chalu rehna chahiye.
6. **Get started** → signup karo. Workspace mein **Load demo dataset** click karo. Overview mein charts aa jayenge.
7. **Customers** tab mein ID search aur segments dekho.
8. **Prediction lab → Train & evaluate models** click karo. Training complete hone ke baad Customers mein predictions dikhengi.
9. **Data studio** se apna CSV import kar sakte ho. Existing dataset replace hota hai.
10. Stop karne ke liye terminal mein Ctrl+C. Agli baar `start_windows.bat` double-click kar sakte ho.

## Common errors

- **can't open file app.py**: Wrong folder. Terminal mein `dir` chalao. Jahan app.py dikhe wahi correct folder hai. `cd RetailSense` tabhi chalao agar dir mein RetailSense subfolder dikhe.
- **python not recognized**: Python install karke VS Code restart karo; Windows mein `py` available ho to pehli command `py -m venv .venv` use karo.
- **Dependency install fails**: Python 3.12 environment recommended; this build was tested on Python 3.12. If a package has no wheel for your newer Python, install Python 3.12 and use `py -3.12 -m venv .venv` in a fresh extracted folder.
- **Do I need Node.js or API keys?** Nahi. Is project ko dono nahi chahiye.
- **PowerShell execution policy?** Activate script run nahi kar rahe; direct .venv Python commands use karo.
- **Port already in use**: Pehle running app wale terminal mein Ctrl+C. Alternatively app.py ke end mein port=5000 ko 5001 karke matching browser URL kholo.
- **Blank chart / error**: Terminal on rakho, page refresh karo aur Load demo dataset use karo.

Demo data synthetic hai. Real-world project findings ke liye UCI dataset import karo, results samjho, phir showcase karo. This is a local portfolio website with separate account workspaces, not a hosted cloud service.
