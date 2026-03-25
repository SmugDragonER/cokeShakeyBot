from dataclasses import dataclass, field

@dataclass
class Player:
    discord_id: int
    name: str
    accounts: dict[str, int] = field(default_factory=dict)


@dataclass
class Team:
    name: str
    main_players: list[Player] = field(default_factory=list)
    sub_players: list[Player] = field(default_factory=list)
    min_main_required: int = 3  # Minimum main players needed to proceed