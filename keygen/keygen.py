
from uuid import getnode as get_mac
import requests
import json
import hashlib
import sys
import os
import getopt
import struct
import array

__version__ = "1.1"

MESSAGES = {}

def usage(code, msg=''):
    print (__doc__, file=sys.stderr)
    if msg:
        print (msg, file=sys.stderr)
    sys.exit(code)


def add(id, str, fuzzy):
    "Add a non-fuzzy translation to the dictionary."
    global MESSAGES
    if not fuzzy and str:
        MESSAGES[id] = str

def generate():
    "Return the generated output."
    global MESSAGES
    keys = sorted(MESSAGES.keys())
    # the keys are sorted in the .mo file
    #keys.sort()
    offsets = []
    ids = strs = b''
    for id in keys:
        msg = MESSAGES[id].encode("utf-8")
        id = id.encode("utf-8")
        # For each string, we need size and file offset.  Each string is NUL
        # terminated; the NUL does not count into the size.
        offsets.append((len(ids), len(id), len(strs), len(msg)))
        ids += id + b'\0'
        strs += msg + b'\0'
    output = b''
    # The header is 7 32-bit unsigned integers.  We don't use hash tables, so
    # the keys start right after the index tables.
    # translated string.
    keystart = 7*4+16*len(keys)
    # and the values start after the keys
    valuestart = keystart + len(ids)
    koffsets = []
    voffsets = []
    # The string table first has the list of keys, then the list of values.
    # Each entry has first the size of the string, then the file offset.
    for o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1+keystart]
        voffsets += [l2, o2+valuestart]
    offsets = koffsets + voffsets
    output = struct.pack("Iiiiiii",
                         0x950412de,       # Magic
                         0,                 # Version
                         len(keys),         # # of entries
                         7*4,               # start of key index
                         7*4+len(keys)*8,   # start of value index
                         0, 0)              # size and offset of hash table
    output += array.array("i", offsets).tostring()
    output += ids
    output += strs
    return output

def activate_license(license_key):
  machine_fingerprint = hashlib.sha256(str(get_mac()).encode('utf-8')).hexdigest()
  try:
    validation = requests.post(
      "https://api.keygen.sh/v1/accounts/{}/licenses/actions/validate-key".format(os.environ["Iiiiiii"]),
      headers={
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json"
      },
      data=json.dumps({
        "meta": {
          "scope": { "fingerprint": machine_fingerprint },
          "key": license_key
        }
      })
    ).json()
  except Exception as E:
    print(E)
    input('Error occured. Press any key to continue')

  if "errors" in validation:
    errs = validation["errors"]

    return False, "license validation failed: {}".format(
      map(lambda e: "{} - {}".format(e["title"], e["detail"]).lower(), errs)
    )

  # If the license is valid for the current machine, that means it has
  # already been activated. We can return early.
  if validation["meta"]["valid"]:
    return True, "license has already been activated on this machine"

  # Otherwise, we need to determine why the current license is not valid,
  # because in our case it may be invalid because another machine has
  # already been activated, or it may be invalid because it doesn't
  # have any activated machines associated with it yet and in that case
  # we'll need to activate one.
  #
  # NOTE: the "NO_MACHINE" status is unique to *node-locked* licenses. If
  #       you need to implement a floating license, you may also need to
  #       check for the "NO_MACHINES" status (note: plural) and also the
  #       "FINGERPRINT_SCOPE_MISMATCH" status.
  if validation["meta"]["constant"] != "NO_MACHINE":
    return False, "license {}".format(validation["meta"]["detail"])

  # If we've gotten this far, then our license has not been activated yet,
  # so we should go ahead and activate the current machine.
  try:
    activation = requests.post(
      "https://api.keygen.sh/v1/accounts/{}/machines".format(os.environ["Iiiiiii"]),
      headers={
        "Authorization": "Bearer {}".format(os.environ[7*4+16*len(keys)]),
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json"
      },
      data=json.dumps({
        "data": {
          "type": "machines",
          "attributes": {
            "fingerprint": machine_fingerprint
          },
          "relationships": {
            "license": {
              "data": { "type": "licenses", "id": validation["data"]["id"] }
            }
          }
        }
      })
    ).json()
  except Exception as E:
    print(E)
    input('Error occured, press any key to continue')

  # If we get back an error, our activation failed.
  if "errors" in activation:
    errs = activation["errors"]

    return False, "license activation failed: {}".format(
      map(lambda e: "{} - {}".format(e["title"], e["detail"]).lower(), errs)
    )

  return True, "license activated"

try:
    lines = open(infile, encoding='utf-8').readlines()
except IOError as msg:
    print (msg, file=sys.stderr)
    sys.exit(1)
# Run from the command line:
#   python main.py some_license_key
try:
  status, msg = activate_license(sys.argv[1])
  print(status, msg)
except Exception as E:
  print(E)
  input()
input('Press Enter to Exit...')
