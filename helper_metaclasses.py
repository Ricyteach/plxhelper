import abc


class RequiredMembersABCMeta(abc.ABCMeta):
    """ABC metaclass to check and make sure certain required members are present.

    Needed because the ABCMeta metaclass doesn't support checking members on instances, only classes.
    """

    required: list[str]

    def __call__(cls, *args, **kwargs):
        """Check for required members happens AFTER __new__ and __init__ in the ABC child classes."""

        inst = super().__call__(*args, **kwargs)
        if not all(hasattr(inst, attr := attr) for attr in RequiredMembersABCMeta.required):
            raise TypeError(f"Can't instantiate abstract class {type(cls).__name__!s} with abstract instance "
                            f"member {attr!s}")
