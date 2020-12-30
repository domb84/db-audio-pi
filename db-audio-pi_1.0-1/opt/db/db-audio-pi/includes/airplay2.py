import subprocess


class airplay():

    def listener(self):
        print("starting")
        cmd = ['/tmp/shairport-sync-metadata-reader/shairport-sync-metadata-reader', '<',
               '/tmp/shairport-sync-metadata']
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        while True:
            output = process.stdout.readline()
            if process.poll() is not None and output == '':
                break
            if output:
                print(output.strip())
        retval = process.poll()
