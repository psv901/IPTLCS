import random
import json
from math import gcd
from cryptography.fernet import Fernet
import matplotlib.pyplot as plt
import base64

v = []
z = []
def encrypt_data(data, public_key):
    encrypted_data = pow(data, public_key[0], public_key[1])
    z.append(int(data))
    v.append(encrypted_data)
    return encrypted_data


def TPC_split(data, id_len):
    p1 = data[:id_len+1]
    p2 = data[id_len+1:]
    return p1, p2

def TPC_chk(N, p2, cur, public_key):
    I = 0
    encrypted_number = str(pow(N, public_key[0], public_key[1]))
    print(encrypted_number)
    for x in cur:
        if x+p2 == encrypted_number:
            I = 1
    return I

def data_split(encMessage):
    d1 = encMessage[:int(len(encMessage) / 2)]
    d2 = encMessage[int(len(encMessage) / 2):]
    return d1, d2



def generate_keypair(p, q):
    n = p * q
    phi = (p-1) * (q-1)
    while True:
        e = random.randint(2, phi-1)
        if gcd(e, phi) == 1:
            break
    d = pow(e, -1, phi)
    return (e, n), (d, n)

def do(veh_id, p2):
    (start,n,I) = (0,3,0)
    index = veh_ids["num"].index(veh_id)
    while start < len(ivsp):
        end = start + n
        if end > len(ivsp):
            end = len(ivsp)
        cur = ivsp[start:end]
        print(cur)
        start += n

        #TPC-chk
        if TPC_chk(veh_id, p2, cur, public_key) == 1:
            I = 1
            break
    if I == 1:

        #retrieve vehicle data
        d2 = veh_ids["data"][index]
        d1 = rsu["data"][index]
        combined = d1+d2
        combined_bytes = base64.b64decode(combined.encode())
        decMessage = fernet.decrypt(combined_bytes).decode()
        print("decrypted string: ", decMessage)
        join_data = json.loads(decMessage)
        print(join_data)
        veh_ids["data"][index] = join_data

    num = str(encrypt_data(veh_id, public_key))

    #TPC-split
    p1, p2 = TPC_split(num, len(num)//2)
    ivsp.append(p1)
    veh_ids["p2s"][index] = p2
    print(ivsp)
    json_str = json.dumps(veh_ids["data"][index])
    print(json_str)
    message = json_str

    #data-split
    encrypted_bytes = fernet.encrypt(message.encode())
    encMessage = base64.b64encode(encrypted_bytes).decode()
    print("original string: ", message)
    print("encrypted string: ", encMessage)
    # split into two parts for storing in RSU and IVSP
    d1, d2 = data_split(encMessage)
    rsu["data"].append(d1)
    veh_ids["data"][index] = d2
    print(d1)
    print(d2)


#at intersection
ivsp = [" "]
p = 157
q = 131
public_key, private_key = generate_keypair(p, q)
key = Fernet.generate_key()
fernet = Fernet(key)
rsu = {
    "data":[]
}
veh_ids = {
    "num" : [23, 45, 12, 24, 49],
    "p2s" : ["000", "000", "000","000", "000"],
    "data" : ["1, 34.5, 6, 1","2, 31.5, 4, 2","3, 12.5, 7, 2","3, 12.5, 7, 2","3, 12.5, 7, 2"]
}

#each vehicle at intersectin
for i,j in zip(veh_ids["num"],veh_ids["p2s"]):
    do(i,j)

#if same vehicle appearing at other intersection
do(veh_ids["num"][0],veh_ids["p2s"][0])


#graph
# Generate x-axis values
x = range(len(v))

# Plot encrypted data values
plt.plot(x, v)

# Add title and labels
plt.title('Encrypted Data Values')
plt.xlabel('Index')
plt.ylabel('Value')

# Display the graph
plt.show()




