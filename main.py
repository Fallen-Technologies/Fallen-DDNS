import os
import requests
import time
import urllib3
from sqlalchemy import create_engine, Column, Integer, String, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Suppress InsecureRequestWarning for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

# Get DB connection info from environment variables
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")
ALERTS_API_KEY = os.getenv("ALERTS_API_KEY")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?client_encoding=utf8"

engine = create_engine(DATABASE_URL)
Base = declarative_base()

class CurrentIP(Base):
    __tablename__ = "current_ip"
    id = Column(Integer, primary_key=True)
    ip_address = Column(String, nullable=False)


# Create table if it doesn't exist
def create_table_if_not_exists():
    inspector = inspect(engine)
    if "current_ip" not in inspector.get_table_names():
        Base.metadata.create_all(engine)
        print("Table 'current_ip' created.")
    else:
        print("Table 'current_ip' already exists, skipping creation.")


def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org")
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching public IP: {e}")
        return None


def check_ip_loop():
    errors = 0
    first_check = True
    while True:
        try:
            ip = get_public_ip()
            if ip:
                # Print the current public IP on boot
                if first_check:
                    print(f"Current public IP: {ip}")
                    first_check = False

                # Check if the IP is already in the database
                Session = sessionmaker(bind=engine)
                session = Session()
                existing_ip = session.query(CurrentIP).all()
                if not existing_ip:
                    # If no IP exists, insert the current IP
                    new_ip = CurrentIP(ip_address=ip)
                    session.add(new_ip)
                    session.commit()
                    print(f"No IP set, Seting IP to: {ip}")
                else:
                    # If an IP exists, check if it matches the current IP
                    if existing_ip[0].ip_address != ip:
                        # Send Alert
                        alert_message = (
                            f"IP has changed from {existing_ip[0].ip_address} to {ip}."
                        )
                        # Update the existing IP
                        old_ip = existing_ip[0].ip_address
                        from utils.cloudflare_agent import update_records, update_firewall_rules

                        # Update DNS records
                        dns_status = update_records(old_ip, ip)
                        if dns_status == False:
                            alert_message = (
                                f"Failed to update DNS records from {old_ip} to {ip}."
                            )
                        else:
                            alert_message = (
                                f"DNS records updated successfully from {old_ip} to {ip}."
                            )
                        print(alert_message)
                        
                        # Update firewall access rules
                        firewall_status = update_firewall_rules(old_ip, ip)
                        if firewall_status == False:
                            print(f"Warning: Failed to update some firewall access rules from {old_ip} to {ip}.")
                        else:
                            print(f"Firewall access rules updated successfully from {old_ip} to {ip}.")
                        
                        # Update the IP in the database
                        print(
                            f"IP has changed from {old_ip} to {ip}. Updating in database."
                        )
                        existing_ip[0].ip_address = ip
                        session.commit()
                        print(f"Updated IP in database to: {ip}")
                        print(f"Resuming checks...")

                session.close()

            else:
                print("Failed to retrieve public IP. Retrying in 1 minute...")

        except Exception as e:
            print(f"An error occurred: {e}")
            errors += 1

        # Wait before checking again
        sleep_time = 300  # 5 minutes
        jiggle = int((os.urandom(1)[0] / 255) * 120) - 60  # -60 to +60 seconds
        sleep_time += jiggle
        current_time = datetime.now()
        next_check_time = current_time + timedelta(seconds=sleep_time)
        print(f"Next check scheduled for {next_check_time.strftime('%H:%M:%S')}. Current time: {current_time.strftime('%H:%M:%S')}")
        time.sleep(sleep_time)  # 5 minutes with jiggle


if __name__ == "__main__":
    create_table_if_not_exists()
    print("Fallen-DDNS started")
    check_ip_loop()
