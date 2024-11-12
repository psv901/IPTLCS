#include <openssl/bn.h>
#include <openssl/rsa.h>
#include <crypto++/integer.h>
#include <vector>
#include <string>
#include <tuple>
#include <string>
#include <vector>
#include <utility>
#include <cmath>
#include <cstdlib>
#include <ctime>
#include <utility>
#include <cmath>
#include <vector>
#include <iostream>


#include <iostream>
#include <vector>
#include <string>
#include <cstdlib>
#include <cmath>
#include <algorithm>
#include <random>
#include <map>
#include <json.hpp>
#include <openssl/rsa.h>
#include <openssl/pem.h>
#include <openssl/err.h>
#include <openssl/bn.h>
#include <openssl/aes.h>
#include <openssl/rand.h>
#include <openssl/conf.h>
#include <openssl/evp.h>
#include <openssl/err.h>
#include <openssl/sha.h>
#include <openssl/ssl.h>
#include <cstring>
#include <iomanip>
#include <sstream>
#include <bitset>
#include <fstream>
#include <cstring>
#include <ctime>
#include <unistd.h>
#include <sys/time.h>
#include <base64.h>

using namespace std;
using json = nlohmann::json;


int encrypt_data(int data, std::pair<int, int> public_key, std::vector<int>& z, std::vector<int>& v) {
    int encrypted_data = pow(data, public_key.first) % public_key.second;
    z.push_back(data);
    v.push_back(encrypted_data);
    return encrypted_data;
}


std::tuple<std::string, std::string> TPC_split(std::string data, int id_len) {
    std::string p1 = data.substr(0, id_len+1);
    std::string p2 = data.substr(id_len+1);
    return std::make_tuple(p1, p2);
}


int TPC_chk(int N, int p2, std::vector<int> cur, std::pair<int, int> public_key) {
    int I = 0;
    int encrypted_number = pow(N, public_key.first) % public_key.second;
    std::cout << encrypted_number << std::endl;
    for (auto x : cur) {
        if (x + p2 == encrypted_number) {
            I = 1;
        }
    }
    return I;
}


std::tuple<std::string, std::string> data_split(std::string encMessage) {
    std::string d1 = encMessage.substr(0, encMessage.length() / 2);
    std::string d2 = encMessage.substr(encMessage.length() / 2);
    return std::make_tuple(d1, d2);
}


int gcd(int a, int b) {
    if (b == 0) {
        return a;
    }
    return gcd(b, a % b);
}

std::pair<std::pair<int, int>, std::pair<int, int>> generate_keypair(int p, int q) {
    int n = p * q;
    int phi = (p-1) * (q-1);
    std::srand(std::time(nullptr));
    int e;
    while (true) {
        e = std::rand() % (phi-2) + 2;
        if (gcd(e, phi) == 1) {
            break;
        }
    }
    int d = std::pow(e, -1);
    while (d < 0) {
        d += phi;
    }
    return std::make_pair(std::make_pair(e, n), std::make_pair(d, n));
}

void do(int veh_id, std::pair<std::string, std::string> p2, std::vector<std::string>& ivsp,
        std::vector<std::unordered_map<std::string, std::string>>& veh_ids,
        std::unordered_map<std::string, std::string>& rsu,
        std::pair<int, int> public_key, Fernet& fernet) {
    int start = 0, n = 3, I = 0;
    int index = std::distance(veh_ids["num"].begin(), std::find(veh_ids["num"].begin(), veh_ids["num"].end(), std::to_string(veh_id)));
    while (start < ivsp.size()) {
        int end = start + n;
        if (end > ivsp.size()) {
            end = ivsp.size();
        }
        std::vector<std::string> cur(ivsp.begin() + start, ivsp.begin() + end);
        for (auto& s : cur) {
            s = std::to_string(std::stoi(s) + std::stoi(p2.second));
        }
        start += n;

        // TPC-chk
        if (TPC_chk(veh_id, p2, cur, public_key) == 1) {
            I = 1;
            break;
        }
    }
    if (I == 1) {
        // retrieve vehicle data
        std::string d2 = veh_ids["data"][index];
        std::string d1 = rsu["data"][index];
        std::string combined = d1 + d2;
        std::string combined_bytes_str = base64_decode(combined);
        std::string decMessage = fernet.decrypt(combined_bytes_str);
        std::cout << "decrypted string: " << decMessage << std::endl;
        auto join_data = json::parse(decMessage);
        veh_ids["data"][index] = join_data.dump();

        std::string num = encrypt_data(veh_id, public_key);

        // TPC-split
        auto [new_p1, new_p2] = TPC_split(num, num.size() / 2);
        ivsp.push_back(new_p1);
        veh_ids["p2s"][index] = new_p2;
        std::cout << "ivsp: ";
        for (const auto& s : ivsp) {
            std::cout << s << ", ";
        }
        std::cout << std::endl;

        std::string json_str = veh_ids["data"][index];
        std::string message = json_str;

        // data-split
        std::string encMessage = base64_encode(fernet.encrypt(message));
        std::cout << "original string: " << message << std::endl;
        std::cout << "encrypted string: " << encMessage << std::endl;
        // split into two parts for storing in RSU and IVSP
        auto [d1, d2] = data_split(encMessage);
        rsu["data"].push_back(d1);
        veh_ids["data"][index] = d2;
        std::cout << "d1: " << d1 << std::endl;
        std::cout << "d2: " << d2 << std::endl;
    }
}

// function declarations
pair<pair<int, int>, pair<int, int>> TPC_split(string data, int id_len);
int TPC_chk(int N, string p2, vector<string> cur, pair<int, int> public_key);
pair<pair<string, string>, pair<string, string>> data_split(string encMessage);
pair<pair<int, int>, pair<int, int>> generate_keypair(int p, int q);
string encrypt_data(int data, pair<int, int> public_key);
string decrypt_data(string enc_data, pair<int, int> private_key);
void do_function(int veh_id, string p2, vector<string>& ivsp, map<string, vector<string>>& rsu, map<string, vector<string>>& veh_ids, Fernet& fernet);

int main() {
vector<string> ivsp = {""};
int p = 157;
int q = 131;
auto [public_key, private_key] = generate_keypair(p, q);
string key = base64_encode((unsigned char*)public_key.first.to_string().c_str(), public_key.first.to_string().size());
Fernet fernet(key);
map<string, vector<string>> rsu = {
{"data", {}}
};
map<string, vector<string>> veh_ids = {
{"num", {"23", "45", "12", "24", "49"}},
{"p2s", {"000", "000", "000", "000", "000"}},
{"data", {"1, 34.5, 6, 1", "2, 31.5, 4, 2", "3, 12.5, 7, 2", "3, 12.5, 7, 2", "3, 12.5, 7, 2"}}
};

// each vehicle at intersection
for (int i = 0; i < veh_ids["num"].size(); ++i) {
    do_function(stoi(veh_ids["num"][i]), veh_ids["p2s"][i], ivsp, rsu, veh_ids, fernet);
}

// if same vehicle appearing at other intersection
do_function(stoi(veh_ids["num"][0]), veh_ids["p2s"][0], ivsp, rsu, veh_ids, fernet);

return 0;
