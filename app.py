import os
from form_filler.api import app

@app.route('/ver')
def app_ver():
    return "v6-root-test", 200

if __name__ == "__main__":
    # Use PORT env var (or 8000 default) and host 0.0.0.0
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
