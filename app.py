import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'form_filler'))
from api import app

@app.route('/ver')
def app_ver():
    return "v6-root-test", 200

if __name__ == "__main__":
    # Use PORT env var (or 8000 default) and host 0.0.0.0
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)
