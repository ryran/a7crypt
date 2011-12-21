#!/usr/bin/env python
# a4crypt v0.5.5 last mod 2011/12/21
# Latest version at <http://github.com/ryran/a7crypt>
# Copyright 2011 Ryan Sawhill <ryan@b19.org>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License <gnu.org/licenses/gpl.html> for more details.
#------------------------------------------------------------------------------

# TODO: SCRIPT docstring

# All Standard Library
from collections import namedtuple
from os.path import isfile
from os import environ, pathsep, access, X_OK, pipe, write, close
from getpass import getpass
from shlex import split
from subprocess import Popen, PIPE, STDOUT


class a4crypt:

    """Provide cmdline wrapper for symmetric {en,de}cryption functions of GPG.
    
    This simply aims to make GPG1/GPG2 symmetric ASCII encryption in terminals
    easier and more fun. (Actually, this was just an excuse for a project in my
    fiZ week of learning python, but hey. ...)
    
    Instantiate this class with color=False if you like spam.
    
    The most important method here is main() -- it will launch an interactive
    prompt and take care of everything for you. That said, you can set the
    proper attribute or two and launch the processing method yourself. ...
    
    And that method would be launch_gpg() which does the actual encryption &
    decryption. To use it directly, save your input to 'a4crypt.inputdata'
    (simple text or file-objects welcome; lists are not), then run:
        launch_gpg(mode, passphrase)
    where mode is either e or d and passphrase is, well... you know.
    
    Once you do that, the passphrase is stored in a OS file descriptor (which
    gpg itself reads directly from) and the input data is passed directly to gpg
    as stdin. Point being, none of your data ends up out in the filesystem.
    
    """

    def __init__(self, color=True):
        """Decide GPG or GPG2 and define class attrs."""
        # Attr which we will store input for gpg in later
        self.inputdata = ''
        # Color makes it a lot easier to distinguish input & output
        Colors = namedtuple('Colors', 'Z B p r b g c')
        if color:
            self.c = Colors(       # Zero, Bold, purple, red, blue, green, cyan
                Z='\033[0m', B='\033[0m\033[1m', p='\033[1;35m',
                r='\033[1;31m', b='\033[1;34m', g='\033[1;32m', c='\033[0;36m')
        else:
            self.c = Colors('', '', '', '', '', '', '')
        # Check path for gpg, then gpg2; set variable for later
        for d in environ['PATH'] .split(pathsep):
            for p in ('gpg', 'gpg2'):
                if isfile(d+'/'+p) and access(d+'/'+p, X_OK):
                    if p == 'gpg': self.gpg = 'gpg --no-use-agent'
                    else: self.gpg = p
                    return
        else:
            print("{r}Error! This program requires gpg or gpg2 to work. Neither "
                  "were found on your system.{Z}" .format(**self.c._asdict()))
            if __name__ == "__main__": exit()
            return



    def main(self):
        """Load initial prompt and kick off all the other functions."""
        # Banner/question
        print("{0.p}<{gpg}>" .format(self.c, gpg=self.gpg[:4].upper().strip())),
        print("{B}[{r}e{B}]ncrypt, [{r}d{B}]ecrypt, or [{r}q{B}]uit?{Z}"
              .format(**self.c._asdict()))
        # Prompt
        mode = self.test_rawinput(": ", 'e', 'd', 'Q', 'q')
        # QUIT
        if mode in {'q', 'Q'}:
            if __name__ == "__main__":
                exit()
            return
        # ENCRYPT MODE
        elif mode == 'e':
            # Get our message-to-be-encrypted from the user; save to variable
            print("{b}Type or paste message to be encrypted.\nEnd with line "
                  "containing only a triple-semicolon, i.e. {B};;;\n:{Z}"
                  .format(**self.c._asdict())),
            self.inputdata = self.multiline_input(';;;')
            print
            # Get passphrase from the user
            passphrase = self.get_passphrase(confirm=True)
            # Launch our subprocess and print the output
            gpg_output = self.launch_gpg(mode, passphrase)
            print("{0.g}\nEncrypted message follows:\n\n{0.c}{output}{0.Z}"
                  .format(self.c, output=gpg_output))
        # DECRYPT MODE
        elif mode == 'd':
            # Get our encrypted message from the user; save to variable
            print("{b}Paste GPG-encrypted message to be decrypted.\n{B}:{Z}"
                  .format(**self.c._asdict())),
            self.inputdata = self.multiline_input('-----END PGP MESSAGE-----',
                                                  keeplastline=True)
            print
            # Get passphrase from the user
            passphrase = self.get_passphrase(confirm=False)
            # Launch our subprocess and print the output
            gpg_output = self.launch_gpg(mode, passphrase)
            while True:
                if gpg_output:
                    print("{0.g}\nDecrypted message follows:\n\n{0.c}{output}"
                          "{0.Z}\n" .format(self.c, output=gpg_output))
                    break
                else:
                    print("{0.r}Error in decryption process! Try again with a "
                          "different passphrase?{0.Z}" .format(self.c))
                    tryagain = self.test_rawinput("[y/n]: ", 'y', 'n')
                    if tryagain == 'y':
                        passphrase = self.get_passphrase(confirm=False)
                        gpg_output = self.launch_gpg(mode, passphrase)
                    else:
                        break



    def test_rawinput(self, prompt, *args):
        """Test user input. Keep prompting until recieve one of 'args'."""
        prompt = self.c.B + prompt + self.c.Z
        userinput = raw_input(prompt)
        while userinput not in args:
            userinput = raw_input("{0.r}Expecting one of {args}\n{prompt}"
                                  .format(self.c, args=args, prompt=prompt))
        return userinput


    def multiline_input(self, EOFstr, keeplastline=False):
        """Prompt for (and return) multiple lines of raw input.
        
        Stop prompting once receive a line containing only EOFstr. Return input
        minus that last line, unless run with keeplastline=True.
        """
        userinput = []
        userinput.append(raw_input())
        while userinput[-1] != EOFstr:
            userinput.append(raw_input())
        if not keeplastline:
            userinput.pop()
        return "\n".join(userinput)


    def get_passphrase(self, confirm=True):
        """Prompt for a passphrase until user enters something twice.
        
        Skip the second confirmation prompt if run with confirm=False.
        """
        #from getpass import getpass
        while True:
            pwd1 = getpass(prompt="{b}Carefully enter passphrase:{Z} "
                           .format(**self.c._asdict()))
            while len(pwd1) == 0:
                pwd1 = getpass(prompt="{r}You must enter a passphrase:{Z} "
                               .format(**self.c._asdict()))
            if not confirm:
                return pwd1
            pwd2 = getpass(prompt="{b}Repeat passphrase to confirm:{Z} "
                           .format(**self.c._asdict()))
            if pwd1 == pwd2:
                return pwd1
            print("{r}The passphrases you entered did not match!{Z}"
                  .format(**self.c._asdict()))


    def launch_gpg(self, mode, passphrase):
        """Start our GPG or GPG2 subprocess & save/return its output.
        
        Aside from its arguments of a passphrase & a mode of 'e' for encrypt or
        'd' for decrypt, this method reads input from a class attribute called
        'inputdata' which can contain normal non-list data or be a file object.
        """
        #from os import pipe, write, close
        #from shlex import split
        #from subprocess import Popen, PIPE, STDOUT
        fd_in, fd_out = pipe()
        write(fd_out, passphrase) ; close(fd_out)
        if mode == 'e':
            cmd = '{0} --batch --no-tty --yes -a -c --force-mdc --passphrase-fd {1}' \
                  .format(self.gpg, fd_in)
        elif mode == 'd':
            cmd = '{0} --batch --no-tty --yes -d --passphrase-fd {1}' \
                  .format(self.gpg, fd_in)        
        else:
            close(fd_in)
            return "Improper mode specified. Must be one of 'e' or 'd'."
        g = Popen(split(cmd), stdin=PIPE, stdout=PIPE)
        output = g.communicate(input=self.inputdata)[0]
        close(fd_in)
        return output



# BEGIN
if __name__ == "__main__":

    from sys import argv
    if len(argv) == 2 and (argv[1] == '--nocolor' or argv[1] == '-n'):
        a4 = a4crypt(color=False)
    elif len(argv) == 1:
        a4 = a4crypt()
    else:
        print("Run with no arguments to get interactive prompt.\n"
              "Optional argument: --nocolor (alias: -n)")
        exit()

    while True:
        a4.main()

