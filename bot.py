import msvcrt
from time import sleep

num = 0
done = False
while not done:
    print(num)
    num += 1

    if msvcrt.kbhit():
        print("you pressed",msvcrt.getch(),"so now i will quit")
        done = True
    sleep(0.2)