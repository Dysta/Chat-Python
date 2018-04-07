#!/usr/bin/python
import socket
import select

class User:
    def __init__(self, client, addr):
        self.socket = client
        self.addr = addr
        self.logged = False
        self.pseudo = None
        self.canal = None

def clear_n(stri):
    return stri.replace('\n', '')

def clear_esp(stri):
    return stri.replace(' ', '')

def sendToCanal(data, userlist, canal):
    if canal == None:
        return
    for user in userlist:
        if user.logged and user.canal == canal :
            sendToUser(data, user) 

def sendToAll(data, userlist, sender):
    for user in userlist:
        if user.logged : #and user != sender
            sendToUser(data, user)

def sendToUser(data, user):
    user.socket.send(data.encode())


def getUserByPseudo(userlist, pseudo):
    for user in userlist:
        if user.pseudo == pseudo:
            return user
    return None
    
def getUserByClient(userlist, client):
    for user in userlist:
        if user.socket == client:
            return user
    return None

host = ''
port = 7777

main_co = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
main_co.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
main_co.bind((host, port))
main_co.listen(1)

user_list = [] #contain all User instance

client_list = [] #contain all socket client
client_list.append(main_co)

while True:
    client_queue, wlist, elist = select.select(client_list, [], [], 0.05)
    for client in client_queue :
        if client == main_co : #if we have a new client
            try:
                client_co, client_addr = client.accept()
                client_list.append(client_co)
                new_user = User(client_co, client_addr[0])
                user_list.append(new_user)
            except socket.error as msg:
                print("Unable to accept.\n" + str(msg))
    
        else : #we receive a message
            user = getUserByClient(user_list, client)
            data = user.socket.recv(1500).decode("UTF-8")
            data_a = clear_n(data).split(" ", 1)

            if(data_a[0].upper() == "JOIN"):
                if user.canal == None or not user.logged:
                    if len(data_a) > 1:
                        canal = clear_esp(data_a[1])
                        if canal != "":
                            user.canal = canal
                            user.logged = True
                            sendToCanal("JOIN : {} \n".format(user.addr), user_list, canal)
                        else :
                            sendToUser("Vous n'avez pas saisi de canal\n", user)
                    else:
                        sendToUser("Vous n'avez pas saisi de canal\n", user)
                else:
                    sendToUser("Vous etes deja connecte\n", user)

            if(data_a[0].upper() == "PART"):
                if user.logged :
                    user.logged = False
                    old_canal = user.canal
                    user.canal = None
                    sendToCanal("PART : L'utilisateur {} est parti \n".format(user.pseudo), user_list, old_canal)
                    sendToUser("Vous etes deconnecte du canal\n", user)
                else :
                    sendToUser("Connecte nulle part\n", user)

            if(len(data) == 0 or data_a[0].upper() == "QUIT"):
                user.socket.close()
                user_list.remove(user)
                client_list.remove(client)
            
            if(data_a[0].upper() == "MSG"):
                if not user.logged :
                    sendToUser("Vous n'etes pas connecte\n", user)
                elif user.pseudo == None :
                    sendToUser("Vous n'avez pas de pseudo\n", user)
                elif user.canal == None :
                    sendToUser("Vous n'avez pas de canal\n", user)
                else :
                    data = data_a[1].encode("UTF-8")
                    if(data != ""):
                        sendToCanal("{}({}) : {}\n".format(user.pseudo, user.canal, data), user_list, user.canal)
            
            if(data_a[0].upper() == "NICK"):
                if user.pseudo != None:
                    sendToUser("Vous avez deja un pseudo\n", user)
                elif not user.logged:
                    sendToUser("Vous n'etes pas connecte\n", user)
                else:
                    if len(data_a) > 1:
                        pseudo = clear_esp(data_a[1])
                        if pseudo != "":
                            if getUserByPseudo(user_list, pseudo) == None :
                                user.pseudo = pseudo
                                sendToUser("Vous etes maintenant connus sous le pseudo de {} \n".format(user.pseudo), user)
                            else:
                                sendToUser("Pseudo deja utilise\n", user)
                        else:
                            sendToUser("Vous n'avez rien indique\n", user)
                    else:
                        sendToUser("Vous n'avez rien indique\n", user)
            
            if(data_a[0].upper() == "LIST"):
                if not user.logged:
                    sendToUser("Vous n'etes pas connecte\n", user)
                else:
                    sendToUser("Liste des utilisateurs en ligne :\n", user)
                    user_logged = ""
                    for user_co in user_list:
                        if user_co.logged:
                            user_logged += "{} - canal : {}\n".format(user_co.pseudo, user_co.canal)
                    if user_logged != "" :
                        sendToUser(user_logged, user)
                    else:
                        sendToUser("Aucun utilisateur en ligne actuellement\n", user)

            if(data_a[0].upper() == "KICK"):
                if not user.logged:
                    sendToUser("Vous n'etes pas connecte\n", user)
                else:
                    if len(data_a) > 1:
                        pseudo = clear_esp(data_a[1])
                        if pseudo != "":
                            user_to_kick = getUserByPseudo(user_list, pseudo)
                            if user_to_kick != None and user_to_kick.canal == user.canal:
                                user_to_kick.canal = None
                                sendToUser("Vous avez ete exclu par {} \n".format(user.pseudo), user_to_kick)
                            else:
                                sendToUser("Utilisateur non trouve, verifiez que vous etes sur le meme canal\n", user)
                        else:
                            sendToUser("Vous n'avez rien indique\n", user)
                    else:
                        sendToUser("Vous n'avez rien indique\n", user)
            
            if(data_a[0].upper() == "KILL"):
                if not user.logged:
                    sendToUser("Vous n'etes pas connecte\n", user)
                else:
                    if len(data_a) > 1:
                        pseudo = clear_esp(data_a[1])
                        if pseudo != "":
                            user_to_kill = getUserByPseudo(user_list, pseudo)
                            if user_to_kill != None:
                                sendToUser("Vous avez ete exclu par {} \n".format(user.pseudo), user_to_kill)
                                user_list.remove(user_to_kill)
                                user_to_kill.client.close()
                            else:
                                sendToUser("Utilisateur non trouve\n", user)
                        else:
                            sendToUser("Vous n'avez rien indique\n", user)
                    else:
                        sendToUser("Vous n'avez rien indique\n", user)



            print("Recv << " + str(data_a))
            print("Send >> " + str(data_a))
    
