#!/usr/bin/env python
# a4crypt v0.5.1 last mod 2011/12/17
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

# TODO: SCRIPT docstring; chop all print() lines down to 79w
# TODO: Implement GPG reading passphrase from fd instead of tempfile with 
# --passphrase-fd or --command-fd (will have to also make data use that method)

# Methods that are imported when they're needed:
    #from os.path import exists
    #from collections import namedtuple
    #from getpass import getpass
    #from tempfile import TemporaryFile, NamedTemporaryFile
    #from subprocess import Popen, PIPE, STDOUT


class a4crypt:

    """Provide cmdline wrapper for symmetric {en,de}cryption functions of GPG.
    
    This simply aims to make GPG1/GPG2 symmetric ASCII encryption in terminals
    easier and more fun. (Actually, this was just an excuse for a project in my
    first week of learning python, but hey. ...)
    
    Instantiate this class with color=False if you like spam.
    
    The most important method here is main() -- it will launch an interactive
    prompt and take care of everything for you. That said, you can set the
    proper attribute or two and launch the processing method yourself. ...
    
    And that method would be launch_gpg() which does the actual encryption &
    decryption. To use it directly, first save your input to self.inputdata
    (simple text or file-objects welcome; lists are not), then run:
        launch_gpg(mode, passfile)
    where mode is either e or d and passfile is the path to a file containing
    only your passphrase. Grab your output from self.gpg_output.
    
    It would of course be simpler and more secure to just let main() do that
    for you, since it would save the passphrase to a tempfile only readable by
    you, and would delete it as soon as the encryption or decryption is done,
    usually only seconds after the file was created. ... But suit yourself.
    
    """

    def __init__(self, color=True):
        """Define vars we need, incl. colors. Check for GPG or GPG2."""
        self.inputdata = ''
        self.gpg_output = ''
        from collections import namedtuple
        Colors = namedtuple('Colors', 'RST BLD R B G C')
        if color:
            self.c = Colors(
                RST='\033[0m', BLD='\033[0m\033[1m', R='\033[1;31m',
                B='\033[1;34m', G='\033[1;32m', C='\033[0;36m')
        else:
            self.c = Colors('', '', '', '', '', '')
        # Time to check for gpg or gpg2 and set variables accordingly
        # TODO: Should be checking for apps using some bin or PATH variable
        #       instead of hardcoding '/usr/bin/' .. need to find The Right Way
        from os.path import exists
        programs=('gpg', 'gpg2')
        for program in programs:
            if exists('/usr/bin/'+program):
                break
        else:
            print("{0.R}Error! This program requires either gpg or gpg2 to work!{0.RST}") .format(self.c)
            if __name__ == "__main__":
                exit()
            return
        if program == 'gpg':
            self.gpg = 'gpg'
        else:
            self.gpg = 'gpg2'


    def main(self):
        """Load initial prompt and kick off all the other functions."""
        # Initial prompt
        print("{0.BLD}[{0.R}e{0.BLD}]ncrypt, [{0.R}d{0.BLD}]ecrypt, or [{0.R}q{0.BLD}]uit?") .format(self.c)
        mode = raw_input(": " + self.c.RST)
        mode = self.test_prompt(mode, 'e', 'd', 'Q', 'q')

        if mode in {'q', 'Q'}:
            if __name__ == "__main__":
                exit()
            return
        # ENCRYPT MODE
        elif mode == 'e':
            # Get our message-to-be-encrypted from the user; save to variable
            print("{0.B}Type or paste message to be encrypted.\nEnd with line containing only a triple-semicolon, i.e. {0.BLD};;;{0.B}\n:{0.RST}") .format(self.c),
            self.inputdata = self.multiline_input(';;;')
            print
            # Get passphrase from the user; save to tmpfile
            pwd = self.get_passphrase()
            from tempfile import TemporaryFile, NamedTemporaryFile
            passphrasefile = NamedTemporaryFile(bufsize=0)
            passphrasefile.write(pwd)
            # Launch our subprocess and print the output
            self.launch_gpg(mode, passphrasefile.name)
            passphrasefile.close()
            print("{0.G}\nEncrypted message follows:\n\n{0.C}{1}{0.RST}") .format(self.c, self.gpg_output)
        # DECRYPT MODE
        elif mode == 'd':
            # Get our encrypted message from the user; save to variable
            print("{0.B}Paste GPG-encrypted message to be decrypted.\n:{0.RST}") .format(self.c),
            self.inputdata = self.multiline_input('-----END PGP MESSAGE-----',
                                                  keeplastline='yes')
            print
            # Get passphrase from the user; save to tmpfile
            pwd = self.get_passphrase(confirm=False)
            from tempfile import TemporaryFile, NamedTemporaryFile
            passphrasefile = NamedTemporaryFile(bufsize=0)
            passphrasefile.write(pwd)
            # Launch our subprocess and print the output
            self.launch_gpg(mode, passphrasefile.name)
            while True:
                if self.gpg_output:
                    print("{0.G}\nDecrypted message follows:\n\n{0.C}{1}{0.RST}\n") .format(self.c, self.gpg_output)
                    break
                else:
                    print("{0.R}Error in decryption process!\nTry again with a different passphrase?\n{0.RST}[y/n]:") .format(self.c),
                    tryagain = raw_input()
                    tryagain = self.test_prompt(tryagain, 'y', 'n')
                    if tryagain == 'y':
                        pwd = self.get_passphrase(confirm=False)
                        passphrasefile.seek(0)
                        passphrasefile.write(pwd)
                        self.launch_gpg(mode, passphrasefile.name)
                    else:
                        break
            passphrasefile.close()                



    def test_prompt(self, userinput, *args):
        """Test user input. Keep prompting until recieve one of 'args'."""
        while True:
            for desired in args:
                if userinput == desired:
                    return userinput
                else:
                    continue
            else:
                print("{0.R}Expecting one of {1}{0.RST}") .format(self.c, args)
                userinput = raw_input(self.c.BLD + ": " + self.c.RST)


    def multiline_input(self, EOFstr, keeplastline=False):
        """Prompt for (and return) multiple lines of raw input.
        
        Stop prompting once receive a line containing only EOFstr. Return input
        minus that last line, unless run with keeplastline=yes.
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
        from getpass import getpass
        while True:
            pwd1 = getpass(prompt=self.c.B +
                           "Carefully enter passphrase: " + self.c.RST)
            while len(pwd1) == 0:
                pwd1 = getpass(prompt=self.c.R +
                               "You must enter a passphrase: " + self.c.RST)
            if not confirm:
                return pwd1
            pwd2 = getpass(prompt=self.c.B +
                           "Repeat passphrase to confirm: " + self.c.RST)
            if pwd1 == pwd2:
                return pwd1
            print(self.c.R + "The passphrases you entered did not match" +
                  self.c.RST)


    def launch_gpg(self, mode, passfile, returnoutput=False):
        """Start our GPG or GPG2 subprocess & save/return its output."""
        from subprocess import Popen, PIPE, STDOUT
        if mode == 'e':
            g = Popen([self.gpg, '--no-use-agent', '--batch', '--no-tty',
                      '--yes', '-a', '-c', '--force-mdc', '--passphrase-file',
                      passfile], stdin=PIPE, stdout=PIPE)
        elif mode == 'd':
            g = Popen([self.gpg, '--no-use-agent', '--batch', '--no-tty',
                      '--yes', '-d', '--passphrase-file',
                      passfile], stdin=PIPE, stdout=PIPE)
        else:
            return "Improper mode specified. Must be one of 'e' or 'd'."
        self.gpg_output = g.communicate(input=self.inputdata)[0]
        if returnoutput:
            return self.gpg_output
        # In the interest of efficiency, I prefer to save the output to a class
        # variable, instead of returning it. But maybe my assumptions about how
        # python works are wrong...



# BEGIN
if __name__ == "__main__":

    from sys import argv
    if len(argv) == 2 and argv[1] == 'nocolor':
        a4 = a4crypt(color=False)
    elif len(argv) == 1:
        a4 = a4crypt()
    else:
        print("Run with no arguments to get interactive prompt.\n" +
              "Or if you've already done that, fyi there's an optional arg\n" +
              "of 'nocolor', which should be pretty self-explanatory.")
        exit()
    while True:
        a4.main()

