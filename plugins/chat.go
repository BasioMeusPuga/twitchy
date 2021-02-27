package main

import (
	"bufio"
	"crypto/tls"
	"flag"
	"fmt"
	"os"

	irc "github.com/thoj/go-ircevent"
)
var channel string
// const channel = "#dapperedking"
const serverssl = "irc.chat.twitch.tv:6697"

func sendMessage(irccon *irc.Connection) {

	reader := bufio.NewReader(os.Stdin)
	fmt.Print("Enter text: ")
	text, _ := reader.ReadString('\n')
	irccon.Privmsg(channel, text)
}
func writeMessage(irccon *irc.Connection) {
	reader := bufio.NewReader(os.Stdin)
	fmt.Print("Enter text: \n")
	text, _ := reader.ReadString('\n')
	irccon.Action(channel,text)
}

func main() {
    wordPtr := flag.String("c", "#yassuo", "channel")
    authPtr := flag.String("p", "auth", "oauth password")
    nickPtr := flag.String("n", "", "nickname")
  flag.Parse()
  var channel string = *wordPtr
	ircnick1 := *nickPtr
	irccon := irc.IRC(ircnick1, ircnick1)
	irccon.Password = *authPtr
	irccon.VerboseCallbackHandler = false
	irccon.Debug = true
	irccon.UseTLS = true
	irccon.TLSConfig = &tls.Config{InsecureSkipVerify: true}
	irccon.AddCallback("001", func(e *irc.Event) { irccon.Join(channel) })
	irccon.AddCallback("PRIVMSG", func(event *irc.Event) {
		fmt.Printf("%s: %s\n", event.Nick, event.Message())
    //sendMessage(irccon)
	})
  irccon.AddCallback("*", func(e *irc.Event) {
		go func(e *irc.Event) {
			reader := bufio.NewReader(os.Stdin)
			fmt.Print("Enter text: ")
			text, _ := reader.ReadString('\n')
			irccon.Privmsg(channel, text)
		//	sendMessage(irccon)
			}(e)
		})
		err := irccon.Connect(serverssl)
		// sendMessage(irccon)
	if err != nil {
		fmt.Printf("Err %s", err)
		return
	}
	irccon.Loop()
}
