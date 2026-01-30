import os

import sys

import time

import requests

import io

from PIL import Image



# Initialize the Waveshare Driver (using your verified logic)

libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')

if os.path.exists(libdir):

    sys.path.append(libdir)



from waveshare_epd import epd7in5_V2



TARGET_URL = "https://transit.rexdooropener.work/einktrain/render_alt/user1"



def main():

    try:

        epd = epd7in5_V2.EPD()

        epd.init()



        while True:

            try:

                # INCREASED TIMEOUT: Give the server 90 seconds to respond

                print(f"Requesting update... {time.ctime()}")

                response = requests.get(TARGET_URL, timeout=90) 

                

                if response.status_code == 200:

                    # Direct buffer creation (reduces memory usage)

                    img_data = response.content

                    Himage = Image.open(io.BytesIO(img_data))

                    epd.display(epd.getbuffer(Himage))

                    Himage.close()  # Explicit cleanup

                    print("Update Success.")

                else:

                    print(f"Server Busy: {response.status_code}")



            except requests.exceptions.Timeout:

                print("!!! Error: Server took too long to respond.")

            except Exception as e:

                print(f"!!! Connection Error: {e}")



            # Wait 60s before trying again

            time.sleep(60)



    except KeyboardInterrupt:

        epd.sleep()

        sys.exit()



if __name__ == "__main__":

    main()