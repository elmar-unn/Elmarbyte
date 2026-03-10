from dataclasses import dataclass


@dataclass
class Game:
    # mängu andmemudel
    id: int
    title: str
    platform: str
    genre: str
    rating: int
    status: str
    favorite: int
    cover_path: str
    launcher_type: str
    launcher_path: str
    notes: str

    @classmethod
    def from_row(cls, row):
        # sqlite rea teisendus objektiks
        return cls(
            id=row["id"],
            title=row["title"],
            platform=row["platform"],
            genre=row["genre"],
            rating=row["rating"],
            status=row["status"],
            favorite=row["favorite"],
            cover_path=row["cover_path"] or "",
            launcher_type=row["launcher_type"] or "local_file",
            launcher_path=row["launcher_path"] or "",
            notes=row["notes"] or "",
        )