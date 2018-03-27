#!/usr/bin/python
import socket
import select

class User:
    def __init__(self, client, addr):
        self.client = client
        self.addr = addr
        self.logged = False
        self.pseudo = None
        self.canal = []

def clear_n(stri):
    return stri.replace('\n', '')

def sendtoall(data, userlist, sender):
    for user in userlist:
        #if client != sender:
        user.client.send(data.encode())


def getUserByPseudo(userlist, pseudo):
    for user in userlist:
        if user.pseudo == pseudo:
            return user
    return None

host = ''
port = 7777

main_co = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
main_co.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
main_co.bind((host, port))
main_co.listen(1)

user_list = []

while True:
    client_queue, wlist, xlist = select.select([main_co], [], [], 0.05)

    for client in client_queue :
        if client == main_co :
            try:
                client_co, client_addr = client.accept()
                new_user = User(client_co, client_addr[0])
                user_list.append(new_user)
            except socket.error as msg:
                print("Unable to accept.\n" + str(msg))
    
    for user in user_list :
        data = user.client.recv(1500).decode("UTF-8")
        data_a = clear_n(data).split(" ", 1)

        if(data_a[0].upper() == "JOIN"):
            if not user.logged :
                sendtoall("JOIN : {} \n".format(user.addr), user_list, None)
                user.logged = True
            else :
                user.client.send("Deja connecte\n".encode())

        if(data_a[0].upper() == "PART"):
            if user.logged :
                user.logged = False
                sendtoall("PART : L'utilisateur {} est parti \n".format(user.pseudo), user_list, None)
            else :
                user.client.send("Connecte nulle part\n".encode())

        if(len(data) == 0 or data_a[0].upper() == "QUIT"):
            user.client.close()
            user_list.remove(user)
        
        if(data_a[0].upper() == "MSG"):
            if not user.logged :
                user.client.send("Vous n'etes pas connecte\n".encode())
            elif user.pseudo == None :
                user.client.send("Vous n'avez pas de pseudo\n".encode())
            else :
                data = data_a[1].encode("UTF-8")
                if(data != ""):
                    sendtoall(data + "\n", user_list, client)
        
        if(data_a[0].upper() == "NICK"):
            if not user.pseudo == None:
                user.client.send("Vous avez deja un pseudo\n".encode())
            elif not user.logged:
                user.client.send("Vous n'etes pas connecte\n".encode())
            else:
                if len(data_a) > 1:
                    pseudo = data_a[1].replace(" ", "")
                    if pseudo != "":
                        if getUserByPseudo(user_list, pseudo) == None :
                            user.pseudo = pseudo
                            user.client.send("Vous etes maintenant connus sous le pseudo de {} \n".format(user.pseudo).encode())
                        else:
                            user.client.send("Pseudo deja utilise\n".encode())
                    else:
                        user.client.send("Vous n'avez rien indique\n".encode())
                else:
                    user.client.send("Vous n'avez rien indique\n".encode())
        
        if(data_a[0].upper() == "LIST"):
            if not user.logged:
                user.client.send("Vous n'etes pas connecte\n".encode())
            else:
                user.client.send("Liste des utilisateurs en ligne :\n".encode())
                user_logged = ""
                for user_co in user_list:
                    if user_co.logged:
                        user_logged += "{}\n".format(user_co.pseudo)
                if user_logged != "" :
                    user.client.send(user_logged.encode())
                else:
                    user.client.send("Aucun utilisateur en ligne actuellement\n".encode())

        if(data_a[0].upper() == "KILL"):
            
            if not user.logged:
                user.client.send("Vous n'etes pas connecte\n".encode())
            else:
                if len(data_a) > 1:
                    pseudo_to_kill = data_a[1].replace(" ", "")
                    if pseudo != "":
                        user_to_kill = getUserByPseudo(user_list, pseudo_to_kill)
                        if user_to_kill != None:
                            user_to_kill.client.send("Vous avez ete exclu par {} \n".format(user.pseudo).encode())
                            user_list.remove(user_to_kill)
                            user_to_kill.client.close()
                    else:
                        user.client.send("Vous n'avez rien indique\n".encode())
                else:
                    user.client.send("Vous n'avez rien indique\n".encode())



        print("Recv << " + str(data_a))
        print("Send >> " + str(data_a))
    
