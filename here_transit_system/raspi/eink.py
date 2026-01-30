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

                print(f"\n[{time.ctime()}] Requesting update...")

                request_start = time.time()

                

                response = requests.get(TARGET_URL, timeout=90)

                request_end = time.time()

                print(f"  → HTTP request: {(request_end - request_start)*1000:.0f}ms")

                

                if response.status_code == 200:

                    # Direct buffer creation (reduces memory usage)

                    image_start = time.time()

                    img_data = response.content

                    print(f"  → Image size: {len(img_data)/1024:.1f}KB")

                    

                    Himage = Image.open(io.BytesIO(img_data))

                    image_end = time.time()

                    print(f"  → Image decode: {(image_end - image_start)*1000:.0f}ms")

                    

                    display_start = time.time()

                    epd.display(epd.getbuffer(Himage))

                    display_end = time.time()

                    print(f"  → Display update: {(display_end - display_start)*1000:.0f}ms")

                    

                    Himage.close()  # Explicit cleanup

                    total_time = display_end - request_start

                    print(f"✓ Total: {total_time*1000:.0f}ms ({total_time:.2f}s)")


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