import sys
import argparse

parser = argparse.ArgumentParser(description='This script takes two numbers and performs an operation on them.')

# Add arguments for the numbers and the operation
parser.add_argument('filename', type=str, help='The first number')
#parser.add_argument('num2', type=int, help='The second number')
#parser.add_argument('-o', '--operation', choices=['add', 'subtract', 'multiply', 'divide'], default='add', help='The operation to perform')

# Parse the arguments
args = parser.parse_args()
print('you input the file name as ', args.filename)
'''

# Perform the operation
if args.operation == 'add':
    result = args.num1 + args.num2
elif args.operation == 'subtract':
    result = args.num1 - args.num2
elif args.operation == 'multiply':
    result = args.num1 * args.num2
elif args.operation == 'divide':
    if args.num2 == 0:
        print("Division by zero is not allowed.")
        exit()
    result = args.num1 / args.num2
'''
# Print the result
#print(f"The result is: {result}")