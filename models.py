from dataclasses import dataclass, field

@dataclass
class Coach:
    discord_id: int
    name: str

@dataclass
class Player:
    discord_id: int
    name: str
    account: str

@dataclass
class Team:
    name: str
    main_players: list[Player] = field(default_factory=list)
    sub_players: list[Player] = field(default_factory=list)
    coaches: list[Coach] = field(default_factory=list)
    min_main_required: int = 3  # Minimum main players needed to proceed
