from dataclasses import dataclass

class Schema:
    # Signal that this class (and subclasses) are of type Schema
    def __schema__(self):
        pass

    def normalize(self):
        """ Return a dict of non-Model values, in most cases running this on a Schema type should yield a hashable dict. """
        d = {}

        for (name, field_type) in self.__annotations__.items():
            if name == '__normalized__':
                continue

            value = self.__dict__[name]

            # if the type is a subclass of a Model, then get its json and convert to obj
            if '__schema__' in dir(value):
                d[name] = value.normalize()
                continue
            else:
                d[name] = value
        return d