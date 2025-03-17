#classes

class Car:
    def __init__(self, model, year):
        print('object at memory location: ', id(self))
        self.model = model
        self.year = year

    def print_car_info(self):
        print('car info: ', self.model, self.year)

    def __str__(self):
        return f'car model: {self.model} - {self.year}'

    def __repr__(self):
        return f'Car {self.model}:{self.year}'

    def __add__(self, other):
        return Car(self.model + other.model, self.year + other.year)

car1 = Car("BMW", 2019)
car2 = Car("Audi", 2020)
print(car1.model)
print(id(car1))

car1.print_car_info()
car2.print_car_info()

print('Printing car object: ', car1)
print('Printing car object: ', car2)

print('cars: ', [car1, car2])
print('Adding cars: ', car1 + car2)