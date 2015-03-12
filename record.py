import re
from utils import *
from err import *

delrep_len = 10

class Pos():

    def __init__(self, pos='', tpos=0):

        self.pos = pos
        self.tpos = tpos         # respect to exon boundary, non-zero value indicates the position is relative to exon boundary

    def __repr__(self):
        if self.tpos < 0:
            return '%s%d' % (str(self.pos), self.tpos)
        elif self.tpos > 0:
            return '%s+%d' % (str(self.pos), self.tpos)
        else: return str(self.pos)

    def __eq__(self, other):
        if (self.pos == other.pos and
            self.tpos == other.tpos):
            return True
        else:
            return False

    def included_plus(self):
        if self.tpos > 0:
            return self.pos + 1
        else:
            return self.pos

    def included_minus(self):
        if self.tpos < 0:
            return self.pos - 1
        else:
            return self.pos

def same_intron(p1, p2):

    if ((p1.included_minus() == p2.included_minus()) and
        (p1.tpos != 0) and (p2.tpos != 0)):
        return True
    else:
        return False

def append_inf(f, a):
    if f:
        return f+';'+a
    else:
        return a

class RegAnno():

    """ annotation of a single site
    generated by Transcript.describe()
    """

    def __init__(self):
        self.exonic = False 
        self.exon = None
        self.cds = False        # whether in CDS
        self.UTR = None         # '3' or '5'

        self.intronic = False
        self.intron_exon1 = None
        self.intron_exon2 = None
        self.intergenic = None  # 'Upstream' or 'Downstream'
        self.splice = None      # 'NextToDonor' | 'Donor' | 'Acceptor' | 'NextToAcceptor'

    def format(self):
        f = ''
        if self.UTR: f = append_inf(f, '%s-UTR' % self.UTR)
        if self.intronic:
            f = append_inf(f, 'Intronic_%d_%d' %
                           (self.intron_exon1, self.intron_exon2))
        elif self.exonic:
            if self.cds:
                f = append_inf(f, 'Exonic_%d' % self.exon)
            else:
                f = append_inf(f, 'CDS_%d' % self.exon)
        elif self.intergenic:
            f = append_inf(f, 'Intergenic%s' % self.intergenic)

        return f

class RegSpanAnno():

    """ annotation of a span
    generated by Transcript.describe_span()
    """

    def __init__(self):

        # self.whole_gene = False
        self.b1 = None         # boundary 1, an object of RegAnno
        self.b2 = None         # boundary 2, an object of RegAnno
        self.transcript_regs = [] # covered parts of a transcript

    def in_UTR(self):

        return (self.b1.UTR and self.b2.UTR and self.b1.UTR == self.b2.UTR)

    def in_exon(self):

        return (self.b1.exonic and
                self.b2.exonic and
                self.b1.exon == self.b2.exon)

    def in_intron(self):

        return (self.b1.intronic and
                self.b2.intronic and
                self.b1.intron_exon1 == self.b2.intron_exon1 and
                self.b1.intron_exon2 == self.b2.intron_exon2)

    def intergenic(self):

        return (self.b1.intergenic and
                self.b2.intergenic and
                self.b1.intergenic == self.b2.intergenic)

    def format(self):

        f = ''
        if self.in_UTR():
            f = append_inf(f, '%s-UTR' % self.b1.UTR)
        if self.in_exon():
            if self.b1.cds and self.b2.cds:
                f = append_inf(f, 'CDS_%d' % self.b1.exon)
            else:
                f = append_inf(f, 'Exonic_%d' % self.b1.exon)
        elif self.in_intron():
            f = append_inf(f, 'Intronic_%d_%d' %
                           (self.b1.intron_exon1, self.b1.intron_exon2))
        elif self.intergenic():
            f = append_inf(f, 'Intergenic_%s' % self.b1.intergenic)
        else:
            f = append_inf(f, 'Other_%s_%s_covering_%s' % 
                           (self.b1.format(), self.b2.format(),
                            ';'.join(self.transcript_regs)))

        return f

def parse_pos(posstr):

    if posstr.isdigit():
        p = Pos()
        p.pos = int(posstr)
        p.tpos = 0
    else:
        m = re.match(r'(\d+)([+-]\d+)', posstr)
        if not m: err_raise(InvalidInputError, 'Invalid position string %s.' % posstr, __name__)
        p = Pos()
        p.pos = int(m.group(1))
        p.tpos = int(m.group(2))

    return p

class Query(object):

    def __init__(self):

        """ for a region by default, no mutation information included """
        self.beg = ''
        self.end = ''
        self.op = None
        self.is_codon = True
        self.gn_name = None
        self.tpt = ''

    def set_pos(self, pos_str):

        if (pos_str.isdigit() and int(pos_str) > 0):
            self.pos = int(pos_str)
            return True
        else:
            err_warn('Abnormal position %s. skip.\n' % pos_str, __name__)
            return False

class QueryREG(Query):

    def __init__(self):

        super(QueryREG, self).__init__()
        self.beg = ''
        self.end = ''
        self.refseq = ''

class QuerySNV(Query):

    def __init__(self):

        super(QuerySNV, self).__init__()
        self.pos = ''
        self.ref = ''
        self.alt = ''

    def cpos(self):
        return self.pos.pos

class QueryDEL(Query):

    def __init__(self):

        super(QueryDEL, self).__init__()
        self.beg = ''
        self.end = ''
        self.delseq = ''
        # for amino acid
        self.beg_aa = ''
        self.end_aa = ''

class QueryFrameShift(Query):

    def __init__(self):

        super(QueryFrameShift, self).__init__()
        self.pos = None
        self.ref = ''
        self.alt = ''
        self.stop_index = ''

class QueryINS(Query):

    def __init__(self):

        super(QueryINS, self).__init__()
        self.pos = ''           # position of base before
        self.insseq = ''
        # for amino acid level query
        self.beg = ''
        self.beg_aa = ''
        self.end = ''
        self.end_aa = ''

class QueryMNV(Query):

    def __init__(self):

        super(QueryMNV, self).__init__()
        self.beg = ''
        self.beg_aa = ''
        self.end = ''
        self.end_aa = ''
        self.refseq = ''
        self.altseq = ''

class QueryDUP(Query):

    def __init__(self):

        super(QueryDUP, self).__init__()
        self.beg = ''
        self.beg_aa = ''
        self.end = ''
        self.end_aa = ''
        self.dupseq = ''


def normalize_reg(q):

    """ create a sensable region 
    respect to the length of the chromosome """

    if q.beg > reflen(q.tok):
        err_print('Region beg %d greater than chromosome length %d, truncated.'
                  % (q.beg, reflen(q.tok)))
        q.beg = reflen(q.tok)

    if q.end > reflen(q.tok):
        err_print('Region end %d greater than chromosome length %d, truncated.'
                  % (q.end, reflen(q.tok)))
        q.end = reflen(q.tok)
    if q.beg < 0:
        err_print('Region beg %d negative, truncated to 0.')
        q.beg = 0    
    if q.end < 0:
        err_print('Region end %d negative, truncated to 0.')
        q.end = 0    

template = "{r.chrm}\t{r.pos}\t{r.tname}\t{r.reg}\t{gnuc}/{tnuc}/{taa}\t{r.info}"
class Record():

    def __init__(self):

        self.tname = '.'        # transcript name
        self.chrm = '.'         # genomic chromosome
        self.pos = '.'          # genomic position string
        self.reg = '.'          # region
        self.info = '.'         # ;-separated key=value pair

    def tnuc(self):
        """ format in HGVS nomenclature e.g., c.12345A>T """
        s = 'c.'
        if hasattr(self, 'tnuc_range') and self.tnuc_range:
            s += self.tnuc_range
            if s == 'c.': return '.'
        else:
            if hasattr(self, 'tnuc_pos') and self.tnuc_pos: s += str(self.tnuc_pos)
            if hasattr(self, 'tnuc_ref') and self.tnuc_ref: s += self.tnuc_ref
            s += '>'
            if hasattr(self, 'tnuc_alt') and self.tnuc_alt: s += self.tnuc_alt
            if s == 'c.>': return '.'
        return s

    def append_info(self, app):
        if self.info and self.info != '.':
            self.info += ';'+app
        else:
            self.info = app

    def gnuc(self):
        
        """ format in chr1:A12345T """
        s = self.chrm+':g.'
        if hasattr(self, 'gnuc_range') and self.gnuc_range:
            s += self.gnuc_range
        else:
            if hasattr(self, 'gnuc_pos') and self.gnuc_pos: s += str(self.gnuc_pos)
            if hasattr(self, 'gnuc_ref') and self.gnuc_ref: s += self.gnuc_ref
            s += '>'
            if hasattr(self, 'gnuc_alt') and self.gnuc_alt: s += self.gnuc_alt
        if s == '.:g.>': return '.'
        return s

    def taa(self):
        """ format in HGVS nomenclature e.g., p.E545K """
        s = 'p.'
        if hasattr(self, 'taa_range') and self.taa_range:
            s += self.taa_range
        else:
            if hasattr(self, 'taa_ref') and self.taa_ref: s += self.taa_ref
            if hasattr(self, 'taa_pos') and self.taa_pos: s += str(self.taa_pos)
            if hasattr(self, 'taa_alt') and self.taa_alt: s += self.taa_alt
        if s == 'p.': return '.'
        return s

    def format_id(self):
        return '%s/%s/%s' % (self.gnuc(), self.tnuc(), self.taa())

    def format(self, op):
        s = op+'\t' if op else ''
        s += template.format(r=self,
                             gnuc=self.gnuc(), tnuc = self.tnuc(), taa = self.taa())
        print s

