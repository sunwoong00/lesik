import random

r = random.random()
if 0 < r <= 1/4:
    print("면")
elif 1/4 < r <= 2/4:
    print("밥")
else:
    print("빵")