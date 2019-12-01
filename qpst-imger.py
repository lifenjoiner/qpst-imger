'''
qpst {prefix}_*.img merger
'''

import sys
import os.path
from xml.dom.minidom import parse

#class IMGMerger:

def process_by_xml(file, prefix = 'system'):
    from struct import unpack
    dom = parse(os.path.join(file))
    elems_program = dom.getElementsByTagName('program')
    basedir = os.path.dirname(file)
    #
    count = len(elems_program)
    img_orders = []
    for i in range(count -1 ):
        file_name = elems_program[i].getAttribute('filename')
        if file_name[0:len(prefix)+1] == prefix + '_':
            n = int( file_name[file_name.find('_')+1:file_name.find('.')] )
            img_orders.append([n, i])
    if len(img_orders) == 0:
        print('No match: ' + prefix)
        return False
    # assume it's messy
    img_orders.sort()
    #print img_orders
    #
    cur_pos_sector = 0
    base_sector = 0
    total_sectors = 0
    for img_order in img_orders:
        i = img_order[1]
        elem = elems_program[i]
        file_name = elem.getAttribute('filename')
        file_sector_offset = int( elem.getAttribute('file_sector_offset') )
        start_sector = int( elem.getAttribute('start_sector') )
        num_partition_sectors = int( elem.getAttribute('num_partition_sectors') )
        if cur_pos_sector == 0:
            base_sector = start_sector
            SECTOR_SIZE_IN_BYTES = int( elem.getAttribute('SECTOR_SIZE_IN_BYTES') ) # must be the same
        print('> ' + file_name)
        #
        print('>> reading...')
        #size = num_partition_sectors * SECTOR_SIZE_IN_BYTES
        try:
            in_file = open(os.path.join(basedir, file_name), 'rb')
            in_data = in_file.read()
            in_file.close()
        except IOError:
            print('<< failed!!!')
            return False
        #
        if cur_pos_sector == 0:
            print('>>> Analysing...')
            if in_data[1080] == '\x53' and in_data[1081] == '\xEF': # Magic signature, 0xEF53
                total_blocks = in_data[1028:1032]
                s_log_block_size = in_data[1048:1052]
                (total_blocks,) = unpack('i', total_blocks)
                (s_log_block_size,) = unpack('i', s_log_block_size)
                total_size = total_blocks * 1024 * pow(2, s_log_block_size)
                total_sectors = total_size / SECTOR_SIZE_IN_BYTES   # same?
                print('<<< Total size(B): %i' % total_size)
            else:
                print('<<< NOT ext4 img!!!')
            #
            out_filename = os.path.join(basedir, prefix + '.img')
            out_file = open(out_filename, 'wb')
        #
        fill_sectors = 0
        if cur_pos_sector > 0 and cur_pos_sector < start_sector:
            fill_sectors = start_sector - cur_pos_sector
        fill_sectors += file_sector_offset
        #
        if fill_sectors > 0:
            print('<< filling...')
            out_file.write(fill_sectors * SECTOR_SIZE_IN_BYTES * '\x00')
        #
        print('<< writing...')
        out_file.write(in_data)
        out_file.flush()
        cur_pos_sector = start_sector + num_partition_sectors
        print('')
    # assure complete
    fill_sectors = base_sector + total_sectors - cur_pos_sector
    if total_sectors > 0 and fill_sectors > 0:
        print('<< extra filling...')
        out_file.write(fill_sectors * SECTOR_SIZE_IN_BYTES * '\x00')
        print('')
    #
    out_file.close()
    #
    print('Finished: ' + out_filename)
    return True

def main(args = None):
    def help(app):
        print('$: merge {prefix}_*.img\n@: 483E10D992F3776521A74B2F64AE2D37 (:\n#: 20161030 v1.0\n')
        print('usage:\n' + app + ' <rawprogram-xml-file> [img-prefix]')
        print('    img-prefix: system (default), factory, cache, userdata ...')
    #
    import sys
    #
    if len(sys.argv) < 2:
        help(sys.argv[0])
        sys.exit(1)
    elif len(sys.argv) == 2:
        prefix = 'system'
    else:
        prefix = sys.argv[2]
    #
    if not os.path.isfile(sys.argv[1]):
        sys.exit('NO file: ' + sys.argv[1])
    #
    process_by_xml(sys.argv[1], prefix)  # ALL should in one file

if __name__ == '__main__':
    main()
