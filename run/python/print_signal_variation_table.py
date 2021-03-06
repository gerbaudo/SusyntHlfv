#!/bin/env python

# Loop over the 'onebin' histograms and make a table with the yield variations
#
# Input: histogram files from plot_emu.py
#
# Example usage:
# > python/print_signal_variation_table.py `ls  out/plot_emu/Jul_06/unblinded/*root | grep signaltaumu | grep sr_mue`
#
# davide.gerbaudo@gmail.com
# Jul 2015

import optparse
import os
import re
import sys

from collections import OrderedDict


import rootUtils as ru
r = ru.importRoot()

def main():
    ""
    all_input_files = [File(f) for f in sys.argv[1:]]
    samples = list(set(f.sample for f in all_input_files))
    linebreak = 60*'-'
    for sample in samples:
        input_files = OrderedDict((f.variation, f) for f in all_input_files if f.sample==sample)
        if 'NOM' not in input_files:
            print "%s is without nominal...no reference to compare against"%(sample)
            continue
        nom_name = input_files['NOM'].filename
        nom_name = os.path.basename(nom_name).replace('.root','')
        nom_yield = input_files['NOM'].get_yield()
        if not nom_yield:
            print "%s has 0.0 nominal yield"%(sample)
            continue

        print "Nominal yield %s  %.2f"%(nom_name, nom_yield)
        print linebreak
        variations = [f.variation for f in input_files.values()]
        max_column_width = max(len(v) for v in variations)
        cellwidth = '%'+str(max_column_width)+'s'
        two_sided_variations = filter_two_sided_variations(variations)
        two_sided_variations_up = [v for v in variations if 'UP' in v]
        one_sided_variations = filter_one_sided_variations(variations, two_sided_variations)

        print "Two-sided variations [%]"+'\n'+linebreak
        for v in sorted(two_sided_variations_up):
            vname = v.replace('_UP', '')
            vup = input_files[v]
            vdo = input_files[v.replace('_UP', '_DOWN')]
            print ' '.join(cellwidth%v for v in [vname,
                                                 "%.2f"%(100.*(vup.get_yield()-nom_yield)/nom_yield),
                                                 "%.2f"%(100.*(vdo.get_yield()-nom_yield)/nom_yield)])
        print linebreak
        print "One-sided variations [%]"
        print linebreak
        for vname in sorted(one_sided_variations):
            vf = input_files[vname]
            print ' '.join(cellwidth%v for v in [vname,
                                                 "%.2f"%(100.*(vf.get_yield()-nom_yield)/nom_yield)])
            # print "%s :  %.2f "%(vname,
            #                      100.*(variation_file.get_yield()-nom_yield)/nom_yield)
    print linebreak

class File(object):
    "A file containing the histogram for a given sample/variation/selection"

    def __init__(self,filename=''):
        if not os.path.exists(filename):
            raise IOError("file not found %s"%filename)
        self.filename = filename
        match = File.parse_attributes(filename)
        for a in ['sample', 'variation', 'region']:
            setattr(self, a, match[a])
        self.histoname_prefix = 'h_onebin'
        self.ptmin = None
        self.ptmax = None
        self.yields = dict()
        self.errors = dict()

    @classmethod
    def parse_attributes(cls, filename=''):
        """extract sample/variation/selection from filename
        Expect a formatting such as:
        - signaltaue_NOM_sr_emu_os_jets.root
        - signaltaumu_JES_UP_sr_emu_os.root
        """
        filename = os.path.basename(filename)
        match = re.search('(?P<sample>\w+?)\_' # non-greedy (assume there's no '_' in the sample name)
                          '(?P<variation>\w+)\_.*'
                          '(?P<region>((?:sr|cr).*))'
                          '\.root',
                          filename)
        if not match:
            raise KeyError("cannot parse sample/variation/region from %s"%filename)
        return {'sample':match.group('sample'),
                'variation':match.group('variation'),
                'region':match.group('region')}
    @property
    def histoname(self):
        return self.histoname_prefix+'_'+self.sample+'_'+self.variation+'_'+self.region

    @property
    def keycache(self):
        ptbin_label = '' if self.ptmin is None and self.ptmax is None else "pt_%03d_%03d"%(self.ptmin, self.ptmax)
        return self.histoname + ptbin_label

    def cache_values(self):
        input_file = r.TFile.Open(self.filename)
        histogram = input_file.Get(self.histoname)
        integral, error = None, None
        ptmin, ptmax = self.ptmin, self.ptmax
        one_dim = histogram.Class().GetName().startswith('TH1')
        if one_dim:
            integral, error = ru.integralAndError(histogram)
        else:
            pt_axis = histogram.GetXaxis()
            if not any(s in pt_axis.GetTitle() for s in ['pt', 'p_T', 'p_{T']):
                raise RuntimeError("expecting pt axis, but got '%s' from %s"%(pt_axis.GetTitle(), histogram.GetName()))
            first_pt_bin = pt_axis.FindFixBin(ptmin) if ptmin else 0
            last_pt_bin = pt_axis.FindFixBin(ptmax) if ptmax else -1
            first_m_bin = 0
            last_m_bin = -1
            error = r.Double(0.0)
            integral = histogram.IntegralAndError(first_pt_bin, last_pt_bin, first_m_bin, last_m_bin, error)
            error = float(error)
        self.yields[self.keycache] = integral
        self.errors[self.keycache] = error
        input_file.Close()

    def get_yield(self):
        key = self.keycache
        if key not in self.yields:
            self.cache_values()
        return self.yields[key]

    def get_error(self):
        key = self.keycache
        if key not in self.yields:
            self.cache_values()
        return self.errors[key]

def filter_two_sided_variations(variations=[]):
    two_sided = []
    for v in variations:
        if 'UP' not in v and 'DOWN' not in v:
            continue
        other = v.replace('DOWN', 'UP') if 'DOWN' in v else v.replace('UP', 'DOWN')
        if other in variations:
            two_sided.append(v)
    return two_sided

def filter_one_sided_variations(variations=[], two_sided=[]):
    two_sided = two_sided if two_sided else two_sided_variations(variations)
    return [v for v in variations if v not in two_sided and v!='NOM']

def test_regex_parsing():
    values = ['signaltaumu_EESZ_UP_sr_emu_os.root',
              'signaltaumu_EESZ_UP_sr_emu_os_jets.root',
              'signaltaumu_NOM_sr_emu_os_jets.root']
    for v in values:
        match = File.parse_attributes(x)
        print x,'  -> ',match
        if match:
            for g in ['sample', 'variation', 'region']:
                print g,': ',match.group(g)


if __name__=='__main__':
    main()
