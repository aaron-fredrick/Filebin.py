class x:
    ...
    
    
a = x()

l = [a, x(), x()]

print(l)

del a

print(l)