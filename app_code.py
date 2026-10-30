#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Poizkusni modul: zbirka majhnih pomožnih funkcij z vgrajenimi testi.

Zagon demo izpisa:
    python3 poizkus.py

Zagon testov:
    python3 -m unittest poizkus.py -v
"""

from __future__ import annotations

import math
import unittest
from typing import Iterable


def fakulteta(n: int) -> int:
    """Vrne n! za n >= 0.

    Dvigne TypeError, če n ni celo število, in ValueError, če je n < 0.
    """
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError("n mora biti celo število")
    if n < 0:
        raise ValueError("n mora biti >= 0")
    return math.factorial(n)


def je_prastevilo(n: int) -> bool:
    """Vrne True, če je n praštevilo, sicer False."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False
    meja = math.isqrt(n) + 1
    for i in range(3, meja, 2):
        if n % i == 0:
            return False
    return True


def obrni_besedilo(s: str) -> str:
    """Vrne obrnjen niz. Dvigne TypeError, če vnos ni niz."""
    if not isinstance(s, str):
        raise TypeError("s mora biti niz")
    return s[::-1]


def povprecje(stevila: Iterable[float]) -> float:
    """Vrne aritmetično sredino. Dvigne ValueError pri praznem vnosu."""
    vrednosti = list(stevila)
    if not vrednosti:
        raise ValueError("seznam je prazen")
    return sum(vrednosti) / len(vrednosti)


class TestPomozneFunkcije(unittest.TestCase):
    """Testni primeri za vse funkcije v modulu."""

    def test_fakulteta_veljavni_vnosi(self) -> None:
        self.assertEqual(fakulteta(0), 1)
        self.assertEqual(fakulteta(1), 1)
        self.assertEqual(fakulteta(5), 120)
        self.assertEqual(fakulteta(10), 3628800)

    def test_fakulteta_napacni_vnosi(self) -> None:
        with self.assertRaises(ValueError):
            fakulteta(-1)
        with self.assertRaises(TypeError):
            fakulteta("5")  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            fakulteta(True)  # type: ignore[arg-type]

    def test_je_prastevilo(self) -> None:
        prastevila = [2, 3, 5, 7, 11, 13, 97, 7919]
        sestavljena = [0, 1, 4, 6, 9, 15, 100, 7917]
        for p in prastevila:
            self.assertTrue(je_prastevilo(p), f"{p} bi moralo biti praštevilo")
        for s in sestavljena:
            self.assertFalse(je_prastevilo(s), f"{s} ne bi smelo biti praštevilo")

    def test_obrni_besedilo(self) -> None:
        self.assertEqual(obrni_besedilo(""), "")
        self.assertEqual(obrni_besedilo("abc"), "cba")
        self.assertEqual(obrni_besedilo("Žaba"), "abaŽ")
        with self.assertRaises(TypeError):
            obrni_besedilo(123)  # type: ignore[arg-type]

    def test_povprecje(self) -> None:
        self.assertAlmostEqual(povprecje([1, 2, 3]), 2.0)
        self.assertAlmostEqual(povprecje([2.5, 2.5]), 2.5)
        self.assertAlmostEqual(povprecje((10,)), 10.0)
        with self.assertRaises(ValueError):
            povprecje([])


def _demo() -> None:
    """Kratek demonstracijski izpis rezultatov."""
    print("=== DEMO ===")
    print(f"5! = {fakulteta(5)}")
    print(f"Ali je 97 praštevilo? {je_prastevilo(97)}")
    print(f"Ali je 100 praštevilo? {je_prastevilo(100)}")
    print(f"Obrnjeno 'Parrot': {obrni_besedilo('Parrot')}")
    print(f"Povprečje [4, 8, 15, 16, 23, 42] = {povprecje([4, 8, 15, 16, 23, 42]):.2f}")


if __name__ == "__main__":
    _demo()


nano poizkus.py


python3 poizkus.py


=== DEMO ===
5! = 120
Ali je 97 praštevilo? True
Ali je 100 praštevilo? False
Obrnjeno 'Parrot': torraP
Povprečje [4, 8, 15, 16, 23, 42] = 18.00


python3 -m unittest poizkus.py -v
