#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#   Copyright 2023 Brooks Su
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""The controller and application entry point of the Termtris game.
"""

import os
import sys

import cursor
import color256 as co
from color256 import Color
import termkey
from termkey import getkey, Key

from tt_tetro import Tetro
from tt_backend import TetrisBackend
from tt_panel import ActivePanel, MessagePanel


_SCORE_TABLE = (10, 100, 200, 400, 800)
_LEVEL_TABLE = (1000, 2000, 4000, 8000, 16000, 32000, 64000, 80_000_000)


class Termtris():
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes
    """The controller of the Termtris game.

    The class have only one public method run() which reads keys from input
    and gets appropriate methods of the backend and the panels to process
    the keyboard events.
    """
    def __init__(self, o_row: int, o_col: int, width: int, height: int):
        self.act_panel = ActivePanel(o_row, o_col, width, height)
        self.msg_panel = MessagePanel(
                o_row, o_col + (width + 1) * 2, width, height)
        self.backend = TetrisBackend(width, height)

        self.score: int = 0
        self.highest: int = 0
        self.speed: int
        self.tick: int = 0
        self.stat_sect_row = height - 5


    def _init_msg_panel(self):
        self.msg_panel.put_text('Termtris', align=MessagePanel.CENTER)
        self.msg_panel.add_separator()
        self.msg_panel.put_text(
                'Right:  Move Right\n'
                'Left:   Move Left\n'
                'Up:     Rotate\n'
                'Down:   Speed up Fall\n'
                'Space:  Fall to Ground\n'
                'Enter:  New Game\n'
                'Esc:    Pause Game\n'
                'Ctrl-X: Exit Game')
        self.msg_panel.add_separator()

        self.msg_panel.add_separator(row=self.stat_sect_row)
        self.msg_panel.tetro_pos(self.stat_sect_row + 1, 8)
        self._renew_game_stat()


    def _renew_game_stat(self):
        for i, level, in enumerate(_LEVEL_TABLE):
            if self.score < level:
                self.msg_panel.put_text(
                        'Next Tetro:\n'
                        f'Level: {i + 1}\n'
                        f'Score: {self.score:<6d}\n'
                        f'Highest: {self.highest:<6d}',
                        row=self.stat_sect_row + 1)
                self.msg_panel.refresh_tetro(self.backend.next_tetro)
                self.speed = len(_LEVEL_TABLE) - i
                break


    def _update_score(self, row_num: int):
        self.score += _SCORE_TABLE[row_num]
        if self.score > self.highest:
            self.highest = self.score
        self._renew_game_stat()


    def _new_game(self) -> None | tuple[Tetro, int, int, list[int] | None]:
        self.act_panel.clear()
        res = self.backend.kick_off()
        self.score = 0
        self._update_score(0)
        return res


    def _idle_fall(self) -> None | tuple[Tetro, int, int, list[int] | None]:
        self.tick = (self.tick + 1) % self.speed
        return None if self.tick else self.backend.move_down()


    def _act_response(
        self,
        tetro: Tetro,
        row: int,
        col: int,
        elim_rows: list[int] | None,
    ):
        if elim_rows is not None:  # Current tetro has done
            self.act_panel.merge_tetro()
            if elim_rows:
                self.act_panel.blink_rows(elim_rows, 3, 0.1)
                self.act_panel.remove_rows(elim_rows)
            self._update_score(len(elim_rows))
        self.act_panel.refresh_tetro(tetro, row=row, col=col)


    def run(self):
        """Continuously reads keys from input and gets appropriate functions
        to process these key events. In idle time, makes the current tetro
        to fall down by count ticks.
        """
        key_funcs = {
            Key.NONE: self._idle_fall,
            Key.ENTER: self._new_game,
            Key.ESC: lambda: not termkey.getch(),
            Key.DOWN: self.backend.move_down,
            Key.SPACE: self.backend.fall_down,
            Key.UP: self.backend.rotate,
            Key.RIGHT: self.backend.move_right,
            Key.LEFT: self.backend.move_left,
            Key.CONTROL_D: self.backend.print_grid,
        }
        self.act_panel.show()
        self.msg_panel.show()
        self._init_msg_panel()

        key = getkey()
        while key != Key.CONTROL_X:
            res = key_funcs.get(key, self._idle_fall)()
            if res:  # (tetro, row, col, elim_rows)
                self._act_response(res[0], res[1], res[2], res[3])
            key = getkey(1)


def main():
    """Entry point of the Termtris game.

    Detects terminal environment and makes initial arguments of the game.
    """
    width, height = ((12, 20) if len(sys.argv) < 3 else
                     (int(sys.argv[1]), int(sys.argv[2])))
    if width < 12 or height < 20:
        raise ValueError('The width must be no less than 12 and the height 20')

    scr_width, scr_height = os.get_terminal_size()
    o_row = min((scr_height - (height + 2)) // 2 + 1, 5)
    o_col = (scr_width - (width * 2 + 3) * 2) // 2 + 1
    if o_row <= 0 or o_col <= 0:
        raise EnvironmentError('Screen too small to fit game')

    cursor.switch_screen()
    cursor.clear_screen()
    cursor.hide_cursor()
    co.set_color(Color.DEEP_KHAKI, Color.COFFEE)
    termkey.setparams(echo=False, intr=False)

    try:
        Termtris(o_row, o_col, width, height).run()
    finally:
        termkey.setparams()
        co.reset_color()
        cursor.show_cursor()
        cursor.restore_screen()


if __name__ == '__main__':
    main()
