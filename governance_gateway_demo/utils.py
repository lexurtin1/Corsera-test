import csv
import hashlib
import hmac
import json
from datetime import datetime
from pathlib import Path
from typing import Dict

DEMO_SECRET = b"demo-secret"

INVESTOR_PROFILES = [
    {
        "id": "INV-DAO-001",
        "name": "Atlas Treasury DAO",
        "type": "DAO",
        "domicile": "Cayman Islands",
        "wallet_address": "0xA7D4f0a2b9C3D1e8F45a901234567890abcdef12",
    },
    {
        "id": "INV-FIN-002",
        "name": "Stratus Fintech Holdings",
        "type": "Fintech",
        "domicile": "United Kingdom",
        "wallet_address": "0xB3C7e4219dDFAb00123456789abcdef012345678",
    },
    {
        "id": "INV-SME-003",
        "name": "Harborlight Trading SME",
        "type": "SME",
        "domicile": "Singapore",
        "wallet_address": "0xF1e2234567890abcDEF1234567890abcdef12345",
    },
    {
        "id": "INV-FO-004",
        "name": "North River Family Office",
        "type": "FamilyOffice",
        "domicile": "United States",
        "wallet_address": "0xC0ffee2540B1eCafe001234567890abcdef98765",
    },
]


def generate_order_id() -> str:
    digest = hashlib.sha256(str(datetime.utcnow().timestamp()).encode("utf-8")).hexdigest()
    short = digest[:8].upper()
    return f"ORD-{short}"


def select_investor(order_id: str) -> Dict[str, str]:
    digest = hashlib.sha256(order_id.encode("utf-8")).digest()
    index = digest[0] % len(INVESTOR_PROFILES)
    return INVESTOR_PROFILES[index]


def canonicalize(data: Dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_compliance_packet(order_id: str, record: Dict, export_folder: Path) -> Dict[str, str]:
    export_folder = Path(export_folder)
    export_folder.mkdir(parents=True, exist_ok=True)

    order_info = {
        "id": order_id,
        "uploaded_filename": record.get("uploaded_filename"),
        "mime": record.get("mime"),
        "size_bytes": record.get("size_bytes"),
    }

    investor = select_investor(order_id)

    base_packet = {
        "packet_version": "1.0",
        "generated_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "order": order_info,
        "investor": investor,
        "checks": {
            "kyc_kyb": {
                "pass": True,
                "rationale": "Identity and entity records validated against internal registry.",
            },
            "aml_sanctions": {
                "pass": True,
                "flags": [],
            },
            "ownership_pep": {
                "pass": True,
                "rationale": "No PEP exposure detected across nested ownership layers.",
            },
            "governance": {
                "pass": True,
                "approvals": [
                    {
                        "approver": "OpRisk Desk",
                        "timestamp": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
                    },
                    {
                        "approver": "GS DAP Compliance",
                        "timestamp": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
                    },
                ],
            },
        },
        "decision": "APPROVED",
    }

    canonical_bytes = canonicalize(base_packet)
    packet_hash = hashlib.sha256(canonical_bytes).hexdigest()
    signature = hmac.new(DEMO_SECRET, canonical_bytes, hashlib.sha256).hexdigest()

    packet = dict(base_packet)
    packet["packet_hash"] = packet_hash
    packet["signature"] = signature

    json_filename = f"packet_{order_id}.json"
    json_path = export_folder / json_filename
    json_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")

    csv_filename = f"packet_{order_id}.csv"
    csv_path = export_folder / csv_filename
    with csv_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Section", "Field", "Value"])
        writer.writerow(["Order", "Order ID", order_info["id"]])
        writer.writerow(["Order", "Filename", order_info["uploaded_filename"]])
        writer.writerow(["Order", "Size (bytes)", order_info["size_bytes"]])
        writer.writerow(["Investor", "Name", investor["name"]])
        writer.writerow(["Investor", "Type", investor["type"]])
        writer.writerow(["Investor", "Domicile", investor["domicile"]])
        writer.writerow(["Investor", "Wallet", investor["wallet_address"]])
        writer.writerow(["Decision", "Status", base_packet["decision"]])
        writer.writerow(["Integrity", "Packet Hash", packet_hash])
        writer.writerow(["Integrity", "Signature", signature])

    return {
        "json_url": f"/exports/{json_filename}",
        "csv_url": f"/exports/{csv_filename}",
        "packet_hash": packet_hash,
        "signature": signature,
    }
