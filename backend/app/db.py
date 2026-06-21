import logging
from pymongo import MongoClient
import bcrypt
from app.config import MONGODB_URI, DATABASE_NAME

logger = logging.getLogger("smart_energy_db")
logging.basicConfig(level=logging.INFO)

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

client = None
db = None

def get_db():
    global client, db
    if db is None:
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        init_db()
    return db

def init_db():
    database = client[DATABASE_NAME]
    
    # 1. Setup Indexes
    # readings composite index: (meterId, timestamp)
    database["readings"].create_index([("meterId", 1), ("timestamp", -1)])
    database["meters"].create_index("serialNumber", unique=True)
    database["users"].create_index("email", unique=True)
    
    # 2. Seed Default Data if empty
    if database["organizations"].count_documents({}) == 0:
        logger.info("Database is empty. Seeding default data...")
        
        # Organizations
        org_id = "org_apex"
        database["organizations"].insert_one({
            "organizationId": org_id,
            "name": "Apex Manufacturing Corp",
            "type": "Industrial"
        })
        
        # Sites
        sites = [
            {
                "siteId": "site_plant_01",
                "organizationId": org_id,
                "name": "Detroit Main Plant",
                "address": "400 Renaissance Ctr, Detroit, MI",
                "timeZone": "Eastern Standard Time"
            },
            {
                "siteId": "site_warehouse_02",
                "organizationId": org_id,
                "name": "Chicago Distribution Center",
                "address": "100 W Randolph St, Chicago, IL",
                "timeZone": "Central Standard Time"
            }
        ]
        database["sites"].insert_many(sites)
        
        # Tariffs
        tariffs = [
            {
                "tariffId": "trf_standard_ind",
                "organizationId": org_id,
                "name": "Industrial Standard Rate",
                "ratePerKwh": 0.12, # $0.12 per kWh
                "effectiveFrom": "2026-01-01T00:00:00Z",
                "effectiveTo": "2027-12-31T23:59:59Z"
            },
            {
                "tariffId": "trf_peak_ind",
                "organizationId": org_id,
                "name": "Peak Hours Surcharge",
                "ratePerKwh": 0.18, # $0.18 per kWh
                "effectiveFrom": "2026-01-01T14:00:00Z",
                "effectiveTo": "2026-12-31T18:00:00Z"
            }
        ]
        database["tariffs"].insert_many(tariffs)
        
        # Users (Admin, Manager, Engineer)
        users = [
            {
                "userId": "usr_admin",
                "name": "Alice Cooper (Admin)",
                "email": "admin@apex.com",
                "passwordHash": get_password_hash("admin123"),
                "role": "Admin",
                "organizationId": org_id,
                "createdAt": "2026-06-21T00:00:00Z"
            },
            {
                "userId": "usr_manager",
                "name": "Bob Marley (Manager)",
                "email": "manager@apex.com",
                "passwordHash": get_password_hash("manager123"),
                "role": "Manager",
                "organizationId": org_id,
                "createdAt": "2026-06-21T00:00:00Z"
            },
            {
                "userId": "usr_engineer",
                "name": "Charlie Brown (Engineer)",
                "email": "engineer@apex.com",
                "passwordHash": get_password_hash("engineer123"),
                "role": "Engineer",
                "organizationId": org_id,
                "createdAt": "2026-06-21T00:00:00Z"
            }
        ]
        database["users"].insert_many(users)
        
        # Meters
        meters = [
            {
                "meterId": "mtr_detroit_hvac",
                "siteId": "site_plant_01",
                "serialNumber": "MTR-DET-HVAC-01",
                "label": "Main Plant HVAC Meter",
                "status": "Active",
                "registeredAt": "2026-06-21T00:00:00Z",
                "deviceToken": "token_det_hvac_01"
            },
            {
                "meterId": "mtr_detroit_assembly",
                "siteId": "site_plant_01",
                "serialNumber": "MTR-DET-ASM-02",
                "label": "Assembly Line B Power Meter",
                "status": "Active",
                "registeredAt": "2026-06-21T00:00:00Z",
                "deviceToken": "token_det_asm_02"
            },
            {
                "meterId": "mtr_chicago_light",
                "siteId": "site_warehouse_02",
                "serialNumber": "MTR-CHI-LGT-01",
                "label": "Warehouse Lighting Meter",
                "status": "Active",
                "registeredAt": "2026-06-21T00:00:00Z",
                "deviceToken": "token_chi_lgt_01"
            }
        ]
        database["meters"].insert_many(meters)
        
        logger.info("Database seeding completed.")
