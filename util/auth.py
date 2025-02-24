
"""
for url percent encode, they exist in a format where special character are preceded by '%'
They will also exist in hex decimal of ASCII
For example "!" = %21 --> 21 is a hex number --> decimal number will be 33
"""
def decode_percent_password(hex_str):
    password = ""
    idx = 0
    while idx < len(hex_str):
        if hex_str[idx] == '%':
            curr_hex = hex_str[idx+1 : idx+3]
            curr_value = chr(int(curr_hex, 16)) #int(curr_hex, 16) --> convert hex to dec --> chr(then to unicode)
            password += curr_value
            idx += 3
            continue
        password += hex_str[idx]
        idx += 1
    return password


def extract_credentials(request):
    body = request.body.decode('utf-8')

    #get username & password split up --? body_split[0] will be username, bodysplit[1] will be password
    body_split = body.split("&")

    username = body_split[0].split("=")[1]
    encoded_password = body_split[1].split("=")[1]
    password = decode_percent_password(encoded_password)
    return [username, password]


def validate_password(password):
    # check length of the password
    if (len(password) < 8):
        return False

    #12 special characters
    special_characters = ["!", "@", "#", "$", "%", "^", "&", "(", ")", "-", "_", "="]

    lowercase = False
    uppercase = False
    special = False
    digits = False

    #loop thu each char and check if there's invalid character
    #Goal: All 4 above of them should be true --> meet pass requirement
    for character in password:
        if character.isalpha():
            if character.islower():
                lowercase = True
            elif character.isupper():
                uppercase = True
        elif character in special_characters:
            special = True
        elif character.isdigit():
            digits = True
        else:
            return False #invalid characters

    return lowercase and uppercase and special and digits