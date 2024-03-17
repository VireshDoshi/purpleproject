from dataclasses import dataclass
from enum import Enum


@dataclass
class Station:
    name: str
    rightmove: int


class Stations(Enum):
    READING = Station(name="Reading", rightmove=0)
    TWYFORD = Station(name="Twyford", rightmove=0)
    MAIDENHEAD = Station(name="Maidenhead", rightmove=2)
    TAPLOW = Station(name="Taplow", rightmove=1)
    SLOUGH = Station(name="Slough", rightmove=1)
    LANGLEY = Station(name="Langley", rightmove=4)
    # BURNHAM = Station(name="Burnham", length=715)

    def __str__(self):
        return self.name

    @staticmethod
    def from_string(s):
        try:
            return Stations[s]
        except KeyError:
            raise ValueError()

    @staticmethod
    def list():
        stations_list = list(map(lambda c: c.value, Stations))
        stations = list(map(lambda c: c.name, stations_list))
        return stations
    
    @staticmethod
    def rightmove_list():
        stations_list = list(map(lambda c: c.value, Stations))
        stationsrm = list(map(lambda c: c.name + '-' + str(c.rightmove), stations_list))
        return stationsrm


