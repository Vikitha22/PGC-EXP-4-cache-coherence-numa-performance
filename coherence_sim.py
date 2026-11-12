#!/usr/bin/env python3

import sys

def make_cores(n=2):
    return [dict() for _ in range(n)]


def access(proto, caches, core, line, op, st):
    me = caches[core]
    state = me.get(line, 'I')

    others = [i for i in range(len(caches)) if i != core]
    holders = [i for i in others if caches[i].get(line, 'I') != 'I']

    if op == 'R':
        if state != 'I':
            return

        st['BusRd'] += 1
        new = 'S'

        for i in holders:
            other_state = caches[i][line]

            if other_state == 'M':
                if proto == 'MOESI':
                    caches[i][line] = 'O'
                    st['c2c'] += 1
                else:
                    caches[i][line] = 'S'
                    st['writeback'] += 1

            elif other_state == 'O':
                st['c2c'] += 1

            elif other_state == 'E':
                caches[i][line] = 'S'

        if not holders and proto in ('MESI', 'MOESI'):
            new = 'E'

        me[line] = new

    else:
        if state == 'M':
            return

        if state == 'E':
            me[line] = 'M'
            st['silent E->M'] += 1
            return

        if state in ('S', 'O'):
            st['BusUpgr'] += 1
        else:
            st['BusRdX'] += 1

            for i in holders:
                other_state = caches[i][line]

                if other_state in ('M', 'O'):
                    if proto == 'MOESI':
                        st['c2c'] += 1
                    else:
                        st['writeback'] += 1

        for i in holders:
            caches[i][line] = 'I'
            st['invalidations'] += 1

        me[line] = 'M'


def run(proto, layout, iters):
    keys = [
        'BusRd', 'BusRdX', 'BusUpgr',
        'silent E->M', 'invalidations',
        'writeback', 'c2c'
    ]

    st = dict.fromkeys(keys, 0)
    caches = make_cores()

    if layout == 'adjacent':
        lx, ly = 'A', 'A'
    else:
        lx, ly = 'A', 'B'

    trace = []

    for _ in range(iters):
        trace += [
            (0, lx, 'R'),
            (0, lx, 'W'),
            (1, ly, 'R'),
            (1, ly, 'W')
        ]

    log = []

    for core, line, op in trace:
        access(proto, caches, core, line, op, st)

        log.append((
            core, line, op,
            caches[0].get('A', 'I'),
            caches[1].get('A', 'I')
        ))

    st['bus transactions'] = (
        st['BusRd'] + st['BusRdX'] + st['BusUpgr']
    )

    return st, log


if __name__ == '__main__':

    iters = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

    print("State trace: first 2 iterations, adjacent layout")

    for proto in ('MSI', 'MESI', 'MOESI'):
        _, log = run(proto, 'adjacent', 2)

        print(f"\n{proto}:")

        for c, line, op, s0, s1 in log:
            print(f"Core {c} {op} -> C0={s0} C1={s1}")

    print(f"\nTotals for {iters} iterations")

    keys = [
        'bus transactions', 'BusRd', 'BusRdX',
        'BusUpgr', 'invalidations',
        'writeback', 'c2c', 'silent E->M'
    ]

    print(f"{'Layout':10} {'Protocol':8} " +
          " ".join(f"{k:>16}" for k in keys))

    for layout in ('adjacent', 'padded'):
        for proto in ('MSI', 'MESI', 'MOESI'):
            st, _ = run(proto, layout, iters)

            print(f"{layout:10} {proto:8} " +
                  " ".join(f"{st[k]:>16}" for k in keys))
