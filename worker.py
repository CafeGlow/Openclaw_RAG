import time
import psycopg2
import requests

def check_and_send_alarms():
    conn = psycopg2.connect("dbname=cafeglow user=postgres password=yourpassword host=localhost")
    cur = conn.cursor()
    # Find users whose alarm time is NOW
    cur.execute("SELECT phone, name FROM users WHERE reminder_time = CURRENT_TIME(0)")
    users_to_ping = cur.fetchall()
    
    for phone, name in users_to_ping:
        # Send a trigger to your OpenClaw WhatsApp endpoint
        print(f"Pinging {name} for their morning dose!")
        # requests.post("http://your-openclaw-ip/send-message", json={"to": phone, "msg": "Time for your Glow Ritual! ☕"})
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    while True:
        check_and_send_alarms()
        time.sleep(60) # Check every minute