import random

def guess():
    l = 1
    h = 10000
    print(f'Choose a number between {l} and {h}')
    guess = random.randint(l,h)
    feedback = str(input(f'Is {guess} too high (h), too low (l), or correct (c): '))
    
    while feedback != 'c':
        if feedback == 'h':
            h = guess
            guess = random.randint(l,h)
            feedback = str(input(f'Is {guess} too high (h), too low (l), or correct (c): '))
        elif feedback == 'l':
            l = guess
            guess = random.randint(l,h)
            feedback = str(input(f'Is {guess} too high (h), too low (l), or correct (c): '))
            
    print(f'{guess} is your number')
        
        
guess()