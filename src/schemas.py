from pydantic import BaseModel


class UserProfile(BaseModel):
    name: str = "Student"
    email: str = "student@example.com"
    bio: str = ""
    energy_drive: str = ""
    information_style: str = ""
