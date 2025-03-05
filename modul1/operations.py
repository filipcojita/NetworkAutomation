# numbers = [1, 2, 4, 5]
# count = False
# for number in numbers.copy():
#     if number == 3:
#         count = True
#     print(number, end=" ")
#
# if count is False:
#         print("3 is not in the list")

# numbers=[1,2,4,5,6,7,8,9]
# count=False
# for number in numbers.copy():
#     if number==3:
#         count=True
# if count is False:
#     print("Did not find number 3")

password = "7780"
login = False
while login is False:
    user_input = input("Enter your password: ")
    if user_input == password:
        login = True
        print("Welcome")
    else:
        print("Wrong password")