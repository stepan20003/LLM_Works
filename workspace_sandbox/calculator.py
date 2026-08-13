class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        else:
            raise TypeError("Unsupported operand type for +")

    def __str__(self):
        return f"Vector({self.x}, {self.y})"

# Example usage:
v1 = Vector(2, 3)
v2 = Vector(4, 5)

result = v1 + v2
print(result)  # Output: Vector(6, 8)