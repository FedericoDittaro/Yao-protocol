#!/usr/bin/python3

# Your scipt should at least have the following functions to show the output

# Assume that two parties involved are Alice and Bob

# This function should print the necessary output from Alice that she wants to send to Bob.
# This ouput from Alice should be printed in a file e.g. file_name
# The output format and how to read it should be described in the report document.
# E.g. if you want to output in table format then describe how to read and interpret the tables. 


def print_alice_to_bob(a_inputs, a_wires, b_keys):
    """
    Prints in the file alice_to_bob.txt Alice's encrypted inputs and Bob's keys
    :param a_inputs: Alice's inputs
    :param a_wires: Alice's wires
    :param b_keys: Bob's keys
    :return: None
    """
    with open('output/alice_to_bob.txt', 'a', encoding='UTF-8') as file:
        file.truncate(0)
        file.write("Alice encrypted inputs are:\n")
        for i, a in enumerate(a_inputs):
            key, encrypted_bit = a_inputs[a_wires[i]]
            file.write(f"Wire {i+1}: Key: {key}, Encrypted Bit: {encrypted_bit}\n")
        file.write("\n\nAlice keys to Bob are: \n")
        for w, ((key_part1, encr_bit1), (key_part2, encr_bit2)) in b_keys.items():
            file.write(f"Wire {w}: (Key: {key_part1}, Encrypted bit: {encr_bit1}), \n\t\t(Key: {key_part2}, Encrypted bit: {encr_bit2})\n\n")



#
# Alice and Bob OT
# This function should print (in a file/console) the OT between Alice and Bob that takes place in Yao's protocol
"""
alice_bob_OT()
"""
    
# This function should print the output the function that Bob wants to compute on the combined data
# For example this could be one of the three functions decribed in the project slide

"""
bob_mpc_compute(bobs_data_input): 
    

alice_mpc_compute(alices_data_input)
"""

# This function should verify whether the output from bob_mpc_compute is same as the ouput
# from a function which is computed non-multiparty way

def read_input(path):
    """
    It reads a file content
    :param path: the path of the file to read.
    :return: It returns the file's data as a list.
    :raises: If the max of the numbers contained in the file exceed 63.
    """
    with open(path, "r", encoding="utf-8") as file:
        input_data = list(map(int, file.readline().split()))
    if max(input_data) > 63:
        raise Exception('The max can not exceed the maximum value stored in 6 bit.')
    return input_data


def write_to_output_file(message='', clear=False):
    """
    It writes a message to a file, appending it to the previous content.
    :param message: the message to write.
    :param clear: if true it clears the file.
    :return: None.
    """
    with open('output/result.txt', 'a', encoding='UTF-8') as file:
        if clear:
            file.truncate(0)
        else:
            file.write(message)


def bin_to_decimal(number):
    """
    It converts the number from binary to decimal
    :param number: a number in base 2 to be converted
    :return: the number converted in base 10
    """
    return(int(str(number), 2))

def verify_output(result):
    """
    It verifies if the result from the garbled circuit is correct, comparing it to
    a simple max computed without multiparty computation
    :param result: the max to verify if is correct or not.
    :return: None.
    """
    alice_data = max(read_input('input/Alice.txt'))
    bob_data = max(read_input('input/Bob.txt'))
    if max(alice_data, bob_data) == result:
        write_to_output_file(f'The max is correct and it is {result}.')
    else:
        write_to_output_file(f'The max is {result} and it is incorrect.')


# If you decide to deviate from this format then you must document the functionality of your script very well so that different steps
# can be verified. 
