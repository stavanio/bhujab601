# Lessons learned

1. **A valid SocketCAN adapter does not need to be reflashed merely because its firmware personality differs from another vendor example.**
2. **Motor IDs do not explain missing physical-layer ACKs.** CAN ACK occurs below application-level ID handling.
3. **A 7/7 motor scan is the strongest early baseline.** Once achieved, stop changing the physical CAN layer.
4. **A 1/7 scan is highly informative.** It proves the PC-to-J1 path and points attention downstream.
5. **Inter-joint braided cables matter.** The motor network must physically continue through the chain.
6. **After USB replug, reinitialize `can0`.**
7. **Do not let two controllers command the arm at once.**
8. **Export parameters before changing them.**
9. **Verify a write by reading it back.**
10. **Start motion tiny and slow.**
11. **Use actual encoder readings to verify home, not commanded targets.**
12. **If STM32 DFU stalls on a direct USB port, a simple USB hub can materially change behavior.**
