"""
Fiefs -- the land a player holds.

A Fief owns no geometry of its own; the layout lives in world/fiefgrid.py. This
class just answers "what is standing on plot NE.C, and how much room is left".

Structures are currently stored as plain data in a sparse dict keyed by plot
address -- only plots with something on them get an entry, and an empty plot is
the absence of a key rather than a key saying "empty". When structures become
real in-game objects that players can enter, they should move to tagged Objects
(tags are Evennia's indexed, queryable store -- see how the xyzgrid contrib
holds coordinates) and only `structures_at` below needs to change.
"""

from evennia.objects.objects import DefaultObject
from evennia.typeclasses.attributes import AttributeProperty

from world import fiefgrid

from .objects import ObjectParent


class Fief(ObjectParent, DefaultObject):
    """
    A square mile of held land, laid out as 9 wards of 9 plots.

    Attributes:
        house: the house holding this fief (see Character.house)
        structures: sparse {plot_address: [{"name": str, "acres": int}, ...]}
    """

    house = AttributeProperty(default="n/a", autocreate=False)
    structures = AttributeProperty(default=dict, autocreate=False)

    def structures_at(self, address):
        """
        Everything standing on a single plot, as a list of plain dicts.

        Copied out of the Attribute deliberately: Evennia hands back _SaverDict
        wrappers, which do not JSON-serialise and would break the OOB payload
        the web map is drawn from. Callers also get values they cannot
        accidentally write back through.
        """
        key = fiefgrid.normalize(address)
        return [dict(entry) for entry in (self.structures or {}).get(key, [])]

    def acres_used(self, address):
        """Acres taken up on a single plot."""
        return sum(s.get("acres", 0) for s in self.structures_at(address))

    def acres_free(self, address):
        """Acres still open on a single plot."""
        return fiefgrid.ACRES_PER_PLOT - self.acres_used(address)

    def ward_summary(self, ward):
        """
        Totals for a whole ward, for the fief-wide overview.

        Aggregates only -- the overview never needs the detail of all 81 plots.
        """
        plots = fiefgrid.plots_in(ward)
        used = sum(self.acres_used(plot) for plot in plots)
        count = sum(len(self.structures_at(plot)) for plot in plots)
        return {
            "ward": fiefgrid.normalize(ward),
            "number": fiefgrid.ward_number(ward),
            "name": fiefgrid.CELL_NAMES[fiefgrid.normalize(ward)],
            "structures": count,
            "acres_used": used,
            "acres_total": fiefgrid.ACRES_PER_WARD,
        }

    def plot_summary(self, address):
        """Detail for a single plot."""
        key = fiefgrid.normalize(address)
        structures = self.structures_at(key)
        return {
            "address": key,
            "spoken": fiefgrid.speak(key),
            "bearing": fiefgrid.bearing(key),
            "structures": structures,
            "acres_used": self.acres_used(key),
            "acres_total": fiefgrid.ACRES_PER_PLOT,
        }

    def add_structure(self, address, name, acres, kind=None):
        """
        Place a structure on a plot, if there is room.

        `kind` is the catalogue key (see world/structures.py), kept alongside
        the display name so later systems can count sawmills without parsing
        prose. Returns (ok, message). Capacity is checked here so every caller
        -- the command, the web UI, a future NPC steward -- gets the same answer.
        """
        key = fiefgrid.normalize(address)
        if fiefgrid.parse_address(key)[1] is None:
            return False, "You must name a single plot, not a whole ward."
        if acres <= 0:
            return False, "A structure must take up at least one acre."
        free = self.acres_free(key)
        if acres > free:
            return False, (
                f"No room: {fiefgrid.speak(key)} has {free} of "
                f"{fiefgrid.ACRES_PER_PLOT} acres open, and that needs {acres}."
            )
        entry = {"name": name, "acres": acres}
        if kind:
            entry["kind"] = kind
        # reassign rather than mutate in place so the Attribute is written back
        current = dict(self.structures or {})
        current[key] = current.get(key, []) + [entry]
        self.structures = current
        return True, f"{name} now stands on {fiefgrid.speak(key)}."

    def remove_structure(self, address, index):
        """
        Pull down the structure at `index` on a plot.

        Which structure that is gets decided by the caller, so the matching
        rules live in one place (the demolish command) rather than being split
        across storage and command layers. Returns (ok, removed_entry).
        """
        key = fiefgrid.normalize(address)
        current = dict(self.structures or {})
        standing = list(current.get(key, []))
        if not 0 <= index < len(standing):
            return False, None
        removed = standing.pop(index)
        if standing:
            current[key] = standing
        else:
            # keep storage sparse: an emptied plot loses its key entirely
            current.pop(key, None)
        self.structures = current
        return True, removed
