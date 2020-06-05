# HasTalk - IPC between Python and Haskell

**HasTalk** is about **IPC** (Inter-Process Communication) with
**Haskell** programs speaking [Nedh](https://github.com/e-wrks/nedh)
(Networked [Edh](https://github.com/e-wrks/edh))

There is a micro protocol for efficient binary/textual packets transport,
then all are scripts in the language each peer is speaking natively.

Only **Python** is supported so far, but any language supporting **eval**
of text script, and **TCP** socket, can easily start out.
