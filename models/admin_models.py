from sqlalchemy import (
    Table, Column, Integer, String, Boolean, DateTime, Date, DECIMAL, Text, Enum, MetaData
)
import enum
from datetime import datetime


metadata = MetaData()

# Enums for choices
class CustomerStatus(enum.Enum):
    contacted = "contacted"
    project_started = "project_started"
    continuing = "continuing"
    finished = "finished"
    rejected = "rejected"
    need_to_call = "need_to_call"


class ConversationLanguage(enum.Enum):
        UZ = "uz"
        RU = "ru"
        EN = "en"

# 3. Customer table
customer = Table(
    "customer",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("full_name", String(500), nullable=False),
    Column("platform", String(255), nullable=False),
    Column("username", String(255), nullable=True),
    Column("phone_number", String(500), nullable=False),
    Column("status", Enum(CustomerStatus), nullable=False),
    Column("assistant_name", String(255), nullable=True),
    Column("notes", Text, nullable=True),
    Column("audio_file_id", String(500), nullable=True),  # Telegram file ID
    Column("audio_url", String(1000), nullable=True),     # (agar kerak bo'lsa)
    Column("conversation_language", Enum(ConversationLanguage), nullable=True, default=ConversationLanguage.UZ),
    Column("created_at", DateTime, nullable=False)
)

